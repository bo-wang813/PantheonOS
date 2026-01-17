"""
Evolution ToolSet - Expose evolution functionality to Agents.

Allows Agents to run evolutionary code optimization on codebases.

Refactored to support:
- Async execution (background evolution with evolution_id tracking)
- Session management (EvolutionManager for multi-evolution coordination)
- Tool visibility control (Agent-visible vs Frontend-only tools)
- Progress polling (frontend queries status via evolution_id)
"""

import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pantheon.toolset import tool, ToolSet
from pantheon.utils.log import logger


# ============================================================================
# Session Management
# ============================================================================

class EvolutionSession:
    """Single evolution session state with self-managed persistence"""
    
    def __init__(self, evolution_id: str, config_dict: Dict[str, Any], workspace_path: Optional[str] = None):
        # === Identification ===
        self.evolution_id = evolution_id
        self.workspace_path = workspace_path
        
        # === Type ===
        self.evolution_type: str = "code"  # "code" | "codebase"
        
        # === Status ===
        self.status = "pending"  # pending/running/completed/failed/cancelled/paused
        self.created_at = time.time()
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self.error: Optional[str] = None
        self.task: Optional[asyncio.Task] = None
        
        # === Input Config ===
        self.evaluator_code: str = ""
        self.objective: str = config_dict.get("objective", "")
        self.max_iter: int = config_dict.get("max_iterations", 100)
        self.num_islands: int = config_dict.get("num_islands", 3)
        self.mutator_model: str = config_dict.get("mutator_model", "normal")
        
        # === Unified File Storage ===
        self.files: Dict[str, str] = {}  # File path -> Content (Unified)
        
        # === Codebase Specific ===
        self.codebase_path: Optional[str] = None
        self.include_patterns: Optional[List[str]] = None
        self.output_path: Optional[str] = None
        
        # === Progress Data ===
        self.current_iter: int = 0
        self.best_score: float = 0.0
        self.score_history: List[float] = []
        
        # === Result Data ===
        self.initial_score: Optional[float] = None
        self.improvement: Optional[float] = None
        self.summary: Optional[str] = None
        
        # === Compatibility ===
        self.config_dict = config_dict  # Keep for other configurations
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize session to dictionary"""
        return {
            "evolution_id": self.evolution_id,
            "evolution_type": self.evolution_type,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
            # Input
            "evaluator_code": self.evaluator_code,
            "objective": self.objective,
            "max_iter": self.max_iter,
            "num_islands": self.num_islands,
            "mutator_model": self.mutator_model,
            # Unified file storage
            "files": self.files,
            # Codebase-specific
            "codebase_path": self.codebase_path,
            "include_patterns": self.include_patterns,
            "output_path": self.output_path,
            # Progress
            "current_iter": self.current_iter,
            "best_score": self.best_score,
            "score_history": self.score_history,
            # Result
            "initial_score": self.initial_score,
            "improvement": self.improvement,
            "summary": self.summary,
            # Compatibility
            "config_dict": self.config_dict,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], workspace_path: Optional[str] = None) -> "EvolutionSession":
        """Deserialize session from dictionary"""
        session = cls(
            evolution_id=data["evolution_id"],
            config_dict=data.get("config_dict", {}),
            workspace_path=workspace_path,
        )
        # Type
        session.evolution_type = data.get("evolution_type", "code")
        # Status
        session.status = data.get("status", "pending")
        session.created_at = data.get("created_at", time.time())
        session.started_at = data.get("started_at")
        session.completed_at = data.get("completed_at")
        session.error = data.get("error")
        # Input
        session.evaluator_code = data.get("evaluator_code", "")
        session.objective = data.get("objective", "")
        session.max_iter = data.get("max_iter", 100)
        session.num_islands = data.get("num_islands", 3)
        session.mutator_model = data.get("mutator_model", "normal")
        # Unified file storage
        session.files = data.get("files", {})
        # Codebase-specific
        session.codebase_path = data.get("codebase_path")
        session.include_patterns = data.get("include_patterns")
        session.output_path = data.get("output_path")
        # Progress
        session.current_iter = data.get("current_iter", 0)
        session.best_score = data.get("best_score", 0.0)
        session.score_history = data.get("score_history", [])
        # Result
        session.initial_score = data.get("initial_score")
        session.improvement = data.get("improvement")
        session.summary = data.get("summary")
        return session
    
    def save(self) -> None:
        """Save session state to disk"""
        if not self.workspace_path:
            return
        
        session_file = Path(self.workspace_path) / "session_state.json"
        session_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(session_file, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, workspace_path: str) -> Optional["EvolutionSession"]:
        """Load session state from disk"""
        session_file = Path(workspace_path) / "session_state.json"
        
        if not session_file.exists():
            return None
        
        try:
            with open(session_file) as f:
                data = json.load(f)
            return cls.from_dict(data, workspace_path)
        except Exception as e:
            logger.warning(f"Failed to load session from {session_file}: {e}")
            return None
    
    def update_progress(self, iteration: int, best_score: float, auto_save: bool = True) -> None:
        """Update progress and optionally auto-save"""
        self.current_iter = iteration
        self.best_score = best_score
        
        # Update score_history
        # Ensure we have enough entries (fill with 0 if needed)
        while len(self.score_history) < iteration:
            self.score_history.append(0.0)
        
        # Update or append the score for this iteration
        if iteration > 0:
            if len(self.score_history) >= iteration:
                self.score_history[iteration - 1] = best_score
            else:
                self.score_history.append(best_score)
        
        if auto_save:
            self.save()


class EvolutionManager:
    """Global evolution session manager (singleton)"""
    
    _instance = None
    
    def __init__(self):
        self._sessions: Dict[str, EvolutionSession] = {}
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            # Restore sessions from disk on first initialization
            cls._instance._restore_sessions()
        return cls._instance
    
    def create_session(self, evolution_id: str, config_dict: Dict[str, Any], workspace_path: Optional[str] = None) -> EvolutionSession:
        session = EvolutionSession(evolution_id, config_dict, workspace_path)
        self._sessions[evolution_id] = session
        session.save()  # Auto-save on creation
        return session
    
    def get_session(self, evolution_id: str) -> Optional[EvolutionSession]:
        return self._sessions.get(evolution_id)
    
    def list_sessions(
        self,
        status_filter: Optional[str] = None,
        limit: int = 100,
    ) -> List[EvolutionSession]:
        """List sessions with optional status filter"""
        sessions = list(self._sessions.values())
        
        if status_filter:
            sessions = [s for s in sessions if s.status == status_filter]
        
        # Sort by creation time (newest first)
        sessions = sorted(sessions, key=lambda s: s.created_at, reverse=True)
        
        return sessions[:limit]
    
    def _restore_sessions(self):
        """Restore sessions from evolution_state.json files in workspaces"""
        # This will be called by EvolutionToolSet after workdir is set
        pass
    
    def restore_from_workdir(self, workdir: Path):
        """Scan workdir for evolution workspaces and restore sessions"""
        if not workdir.exists():
            return
        
        logger.info(f"Restoring Evolution sessions from {workdir}")
        restored_count = 0
        
        for evolution_dir in workdir.iterdir():
            if not evolution_dir.is_dir():
                continue
            
            workspace_path = str(evolution_dir)
            
            # Load from session_state.json
            session = EvolutionSession.load(workspace_path)
            
            if session:
                self._sessions[session.evolution_id] = session
                restored_count += 1
        
        if restored_count > 0:
            logger.info(f"Restored {restored_count} Evolution session(s)")


class EvolutionToolSet(ToolSet):
    """
    ToolSet for evolutionary code optimization.

    Allows Agents to evolve codebases through iterative LLM-guided
    mutations and evaluations.

    Example:
        ```python
        from pantheon.agent import Agent
        from pantheon.toolsets.evolution import EvolutionToolSet

        agent = Agent(
            name="optimizer",
            instructions="You help users optimize their code.",
        )
        agent.toolset(EvolutionToolSet("evolve"))

        response = await agent.run("Optimize this sorting function...")
        ```
    """

    def __init__(
        self,
        name: str = "evolution",
        workdir: Optional[str] = None,
        default_iterations: int = 50,
        default_islands: int = 3,
        **kwargs,
    ):
        """
        Initialize the Evolution ToolSet.

        Args:
            name: Name of the toolset
            workdir: Working directory for evolution workspaces
            default_iterations: Default number of evolution iterations
            default_islands: Default number of MAP-Elites islands
        """
        super().__init__(name, **kwargs)
        
        # Use fixed default path for evolution data persistence
        if workdir:
            self.workdir = Path(workdir).expanduser().resolve()
        else:
            from pantheon.settings import get_settings
            settings = get_settings()
            self.workdir = settings.pantheon_dir / "evolution"
        
        # Ensure workdir exists
        self.workdir.mkdir(parents=True, exist_ok=True)
        
        self.default_iterations = default_iterations
        self.default_islands = default_islands
        
        # Global session manager
        self.manager = EvolutionManager.get_instance()
        
        # Restore sessions from disk
        self.manager.restore_from_workdir(self.workdir)
    
    def _get_workspace_path(self, evolution_id: str) -> str:
        """Get workspace path for an evolution (convention: {workdir}/{evolution_id})"""
        return str(self.workdir / evolution_id)
    
    def _estimate_timeout(self, iterations: int) -> int:
        """Estimate timeout for synchronous mode based on iterations"""
        # Assume ~12 seconds per iteration on average
        base_time = iterations * 12
        with_buffer = int(base_time * 1.3)  # Add 30% buffer
        return max(60, min(with_buffer, 300))  # Clamp to 60-300 seconds

    @tool
    async def evolve_code(
        self,
        code: str,
        evaluator_code: str,
        objective: str,
        iterations: Optional[int] = None,
        islands: Optional[int] = None,
        model: str = "normal",
        async_mode: bool = True,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Evolve and optimize code using evolutionary algorithms.

        This tool runs an evolutionary optimization loop that:
        1. Generates mutations of the code using an LLM
        2. Evaluates each mutation using the provided evaluator
        3. Keeps the best-performing variants
        4. Repeats until convergence or max iterations

        Args:
            code: The initial code to optimize (single file content)
            evaluator_code: Python code defining an `evaluate(workspace_path)` function
                that returns a dict with at least a "combined_score" key (0-1 scale).
                Example:
                ```python
                def evaluate(workspace_path):
                    import time
                    exec(open(f"{workspace_path}/main.py").read())
                    # ... run tests or benchmarks ...
                    return {"combined_score": 0.85, "speed": 1.2}
                ```
            objective: Natural language description of the optimization goal.
                Example: "Optimize for speed while maintaining correctness"
            iterations: Maximum number of evolution iterations (default: 50)
            islands: Number of evolution islands for diversity (default: 3)
            model: Model to use for mutation generation
            async_mode: If True, run in background and return immediately (default: True)
            timeout: Timeout in seconds for sync mode (None = auto-estimate)

        Returns:
            dict: Evolution results containing:
                Async mode (async_mode=True):
                    - success: Whether evolution started successfully
                    - evolution_id: Unique ID for tracking
                    - status: "running"
                    - estimated_time: Estimated completion time
                    - message: Status message
                Sync mode (async_mode=False):
                    - success: Whether evolution completed successfully
                    - evolution_id: Unique ID
                    - status: "completed" or "running" (if timeout)
                    - file_count: Number of files (if completed)
                    - best_score: The best score achieved (if completed)
                    - improvement: Score improvement (if completed)
                    - summary: Human-readable summary (if completed)
        """
        # Generate evolution ID
        evolution_id = str(uuid.uuid4())
        iterations = iterations or self.default_iterations
        islands = islands or self.default_islands
        
        # Smart timeout estimation for sync mode
        if timeout is None and not async_mode:
            timeout = self._estimate_timeout(iterations)
        
        # Prepare config
        from pantheon.evolution import EvolutionConfig
        
        workspace_path = self._get_workspace_path(evolution_id)
        config = EvolutionConfig(
            max_iterations=iterations,
            num_islands=islands,
            mutator_model=model,
            workspace_path=workspace_path,
            db_path=workspace_path,  # Enable checkpoint persistence
        )
        
        # Create session with extended config for list_evolutions
        config_dict = config.to_dict()
        config_dict["objective"] = objective  # Save for list_evolutions
        session = self.manager.create_session(evolution_id, config_dict, workspace_path)
        
        # Save input data (unified model)
        session.evolution_type = "code"  # ✅ Set type
        session.files = {"main.py": code}  # ✅ Unified file storage
        session.evaluator_code = evaluator_code
        session.objective = objective
        session.save()
        
        if async_mode:
            # Async mode: start background task and return immediately
            session.task = asyncio.create_task(
                self._run_evolution_background(
                    evolution_id, code, evaluator_code, objective, config
                )
            )
            return {
                "success": True,
                "evolution_id": evolution_id,
                "status": "running",
                "estimated_time": f"~{iterations * 12 // 60} minutes",
                "message": (
                    f"✅ Evolution started successfully!\n\n"
                    f"🆔 Evolution ID: {evolution_id}\n"
                    f"⏱️ Estimated time: ~{iterations * 12 // 60} minutes\n\n"
                    f"📊 To monitor progress:\n"
                    f"1. Click the DNA icon (🧬) in left sidebar\n"
                    f"2. Find evolution in the list\n"
                    f"3. Click to view details\n\n"
                    f"Or use: get_evolution_status('{evolution_id}')"
                ),
            }
        else:
            # Sync mode: wait for completion (with timeout)
            try:
                result = await asyncio.wait_for(
                    self._run_evolution(evolution_id, code, evaluator_code, objective, config),
                    timeout=timeout
                )
                session = self.manager.get_session(evolution_id)
                return {
                    "success": True,
                    "evolution_id": evolution_id,
                    "status": "completed",
                    "file_count": len(session.files),
                    "best_score": result.best_score,
                    "improvement": session.improvement,
                    "summary": session.summary,
                }
            except asyncio.TimeoutError:
                # Timeout: convert to async mode
                session.task = asyncio.create_task(
                    self._run_evolution_background(
                        evolution_id, code, evaluator_code, objective, config
                    )
                )
                return {
                    "success": True,
                    "evolution_id": evolution_id,
                    "status": "running",
                    "message": f"Timeout after {timeout}s, continuing in background.",
                }

    @tool
    async def evolve_codebase(
        self,
        codebase_path: str,
        evaluator_code: str,
        objective: str,
        include_patterns: Optional[List[str]] = None,
        iterations: Optional[int] = None,
        islands: Optional[int] = None,
        model: str = "normal",
        output_path: Optional[str] = None,
        async_mode: bool = True,
    ) -> Dict[str, Any]:
        """
        Evolve and optimize an entire codebase.

        Args:
            codebase_path: Path to the directory containing the codebase
            evaluator_code: Python code defining an `evaluate(workspace_path)` function
            objective: Natural language description of the optimization goal
            include_patterns: Glob patterns for files to include (default: ["**/*.py"])
            iterations: Maximum number of evolution iterations
            islands: Number of evolution islands
            model: Model to use for mutation generation
            output_path: Optional path to save the best result
            async_mode: If True, run in background and return immediately (default: True)

        Returns:
            dict: Evolution results
        """
        from pantheon.evolution import EvolutionConfig, CodebaseSnapshot
        
        # Generate evolution_id
        evolution_id = str(uuid.uuid4())
        iterations = iterations or self.default_iterations
        islands = islands or self.default_islands
        include_patterns = include_patterns or ["**/*.py"]
        
        # Load codebase
        codebase_path = Path(codebase_path).expanduser().resolve()
        if not codebase_path.is_dir():
            return {"success": False, "error": f"Codebase path not found: {codebase_path}"}
        
        try:
            initial_snapshot = CodebaseSnapshot.from_directory(
                str(codebase_path),
                include_patterns=include_patterns,
            )
        except Exception as e:
            return {"success": False, "error": f"Failed to load codebase: {e}"}
        
        logger.info(
            f"Loaded codebase: {initial_snapshot.file_count()} files, "
            f"{initial_snapshot.total_lines()} lines"
        )
        
        # Prepare config
        workspace_path = self._get_workspace_path(evolution_id)
        config = EvolutionConfig(
            max_iterations=iterations,
            num_islands=islands,
            mutator_model=model,
            workspace_path=workspace_path,
            db_path=workspace_path,
        )
        
        # Create session (unified)
        config_dict = config.to_dict()
        config_dict["objective"] = objective
        session = self.manager.create_session(evolution_id, config_dict, workspace_path)
        
        # Set type and data (unified model)
        session.evolution_type = "codebase"  # ✅ Set type
        session.files = initial_snapshot.files  # ✅ Unified file storage
        session.codebase_path = str(codebase_path)  # ✅ Codebase-specific metadata
        session.include_patterns = include_patterns
        session.output_path = output_path
        session.evaluator_code = evaluator_code
        session.objective = objective
        session.save()
        
        # Async/sync execution
        if async_mode:
            session.task = asyncio.create_task(
                self._run_evolution_codebase_background(
                    evolution_id, initial_snapshot, evaluator_code, objective, config, output_path
                )
            )
            return {
                "success": True,
                "evolution_id": evolution_id,
                "status": "running",
                "file_count": initial_snapshot.file_count(),
                "estimated_time": f"~{iterations * 15 // 60} minutes",
                "message": (
                    f"✅ Codebase evolution started successfully!\n\n"
                    f"🆔 Evolution ID: {evolution_id}\n"
                    f"📁 Files: {initial_snapshot.file_count()}\n"
                    f"⏱️ Estimated time: ~{iterations * 15 // 60} minutes\n\n"
                    f"📊 To monitor progress:\n"
                    f"1. Click the DNA icon (🧬) in left sidebar\n"
                    f"2. Find evolution in the list\n"
                    f"3. Click to view details\n\n"
                    f"Or use: get_evolution_status('{evolution_id}')"
                ),
            }
        else:
            # Sync execution
            try:
                result = await self._run_evolution_codebase(
                    evolution_id, initial_snapshot, evaluator_code, objective, config, output_path
                )
                return {
                    "success": True,
                    "evolution_id": evolution_id,
                    "status": "completed",
                    "file_count": len(session.files),
                    "best_score": result.best_score,
                    "improvement": session.improvement,
                    "summary": session.summary,
                }
            except Exception as e:
                logger.error(f"Codebase evolution failed: {e}")
                return {
                    "success": False,
                    "evolution_id": evolution_id,
                    "error": str(e),
                }
    
    
    # ===== Internal Methods =====
    
    async def _run_evolution(
        self,
        evolution_id: str,
        code: str,
        evaluator_code: str,
        objective: str,
        config,
    ):
        """Execute evolution (wait for completion)"""
        from pantheon.evolution import EvolutionTeam
        
        session = self.manager.get_session(evolution_id)
        session.status = "running"
        session.started_at = time.time()
        
        try:
            # Define progress callback to update session state in real-time
            def on_progress(iteration: int, best_score: float):
                """Called periodically during evolution (every checkpoint_interval)"""
                session.update_progress(iteration, best_score, auto_save=True)
                logger.info(f"Evolution {evolution_id} progress: iteration={iteration}, score={best_score:.4f}")
            
            team = EvolutionTeam(config=config)
            result = await team.evolve(
                initial_code=code,
                evaluator_code=evaluator_code,
                objective=objective,
                progress_callback=on_progress,
            )
            
            session.status = "completed"
            session.completed_at = time.time()
            session.best_score = result.best_score
            session.current_iter = result.total_iterations
            
            # Save result data (unified model)
            session.files = {"main.py": result.best_code}  # ✅ Unified file storage
            
            # Calculate initial_score from score_history
            if session.score_history:
                session.initial_score = session.score_history[0]
                
                # Calculate improvement percentage
                if session.initial_score > 0:
                    session.improvement = ((session.best_score - session.initial_score) / session.initial_score) * 100
                else:
                    session.improvement = 0.0
                
                # Generate summary
                session.summary = (
                    f"Evolution completed in {result.total_iterations} iterations. "
                    f"Score improved from {session.initial_score:.4f} to {session.best_score:.4f} "
                    f"({session.improvement:+.1f}%)."
                )
            else:
                session.initial_score = 0.0
                session.improvement = 0.0
                session.summary = f"Evolution completed in {result.total_iterations} iterations."
            
            session.save()
            
            # Auto-generate HTML report
            try:
                html_path = Path(config.db_path) / "evolution_report.html"
                result.save_html_report(str(html_path))
                logger.info(f"HTML report saved to {html_path}")
            except Exception as e:
                logger.warning(f"Failed to generate HTML report: {e}")
            
            return result
            
        except Exception as e:
            session.status = "failed"
            session.error = str(e)
            logger.error(f"Evolution {evolution_id} failed: {e}")
            raise

    async def _run_evolution_background(self, evolution_id, code, evaluator_code, objective, config):
        """Run evolution in background (non-blocking)"""
        try:
            result = await self._run_evolution(evolution_id, code, evaluator_code, objective, config)
            logger.info(f"Evolution {evolution_id} completed: score={result.best_score:.4f}")
        except asyncio.CancelledError:
            logger.info(f"Evolution {evolution_id} cancelled")
            session = self.manager.get_session(evolution_id)
            if session:
                session.status = "cancelled"
        except Exception as e:
            logger.error(f"Evolution {evolution_id} failed: {e}")
    async def _run_evolution_codebase(
        self, evolution_id, initial_snapshot, evaluator_code, objective, config, output_path
    ):
        """Execute codebase evolution (wait for completion)"""
        from pantheon.evolution import EvolutionTeam
        
        session = self.manager.get_session(evolution_id)
        session.status = "running"
        session.started_at = time.time()
        
        try:
            # Define progress callback
            def on_progress(iteration, best_score):
                session.update_progress(iteration, best_score, auto_save=True)
                logger.info(f"Codebase evolution {evolution_id} progress: iteration={iteration}, score={best_score:.4f}")
            
            team = EvolutionTeam(config=config)
            result = await team.evolve(
                initial_code=initial_snapshot,
                evaluator_code=evaluator_code,
                objective=objective,
                progress_callback=on_progress,
            )
            
            # Save result (unified model)
            session.status = "completed"
            session.completed_at = time.time()
            session.best_score = result.best_score
            session.current_iter = result.total_iterations
            
            # ✅ Unified file storage
            session.files = result.best_program.snapshot.files
            
            # Calculate result data
            if session.score_history:
                session.initial_score = session.score_history[0]
                
                if session.initial_score > 0:
                    session.improvement = ((session.best_score - session.initial_score) / session.initial_score) * 100
                else:
                    session.improvement = 0.0
                
                session.summary = (
                    f"Codebase evolution completed in {result.total_iterations} iterations. "
                    f"Score improved from {session.initial_score:.4f} to {session.best_score:.4f} "
                    f"({session.improvement:+.1f}%). "
                    f"Evolved {len(session.files)} files."
                )
            else:
                session.initial_score = 0.0
                session.improvement = 0.0
                session.summary = f"Codebase evolution completed in {result.total_iterations} iterations."
            
            # Save to output path if requested
            if output_path:
                output_dir = Path(output_path).expanduser().resolve()
                result.best_program.snapshot.to_workspace(str(output_dir))
                session.output_path = str(output_dir)
                logger.info(f"Best codebase saved to {output_dir}")
            
            session.save()
            
            # Auto-generate HTML report
            try:
                html_path = Path(config.db_path) / "evolution_report.html"
                result.save_html_report(str(html_path))
                logger.info(f"HTML report saved to {html_path}")
            except Exception as e:
                logger.warning(f"Failed to generate HTML report: {e}")
            
            return result
            
        except Exception as e:
            session.status = "failed"
            session.error = str(e)
            session.save()
            logger.error(f"Codebase evolution {evolution_id} failed: {e}")
            raise

    async def _run_evolution_codebase_background(
        self, evolution_id, initial_snapshot, evaluator_code, objective, config, output_path
    ):
        """Run codebase evolution in background (non-blocking)"""
        try:
            result = await self._run_evolution_codebase(
                evolution_id, initial_snapshot, evaluator_code, objective, config, output_path
            )
            logger.info(f"Codebase evolution {evolution_id} completed: score={result.best_score:.4f}")
        except asyncio.CancelledError:
            logger.info(f"Codebase evolution {evolution_id} cancelled")
            session = self.manager.get_session(evolution_id)
            if session:
                session.status = "cancelled"
                session.save()
        except Exception as e:
            logger.error(f"Codebase evolution {evolution_id} failed: {e}")

    # ===== Frontend-only Tools =====

    @tool
    async def get_evolution_status(
        self,
        evolution_id: str,
        include_code: bool = False,
    ) -> Dict[str, Any]:
        """
        Query evolution status by ID (frontend polling tool).

        Args:
            evolution_id: Unique evolution identifier
            include_code: Whether to include files and evaluator_code
                         Default False for lightweight polling

        Returns:
            Basic mode (include_code=False):
                - evolution_id, evolution_type, status, iteration, max_iterations
                - best_score, score_history, file_count, improvements_found
                - config (objective, iterations, islands, model)
            
            Complete mode (include_code=True):
                - All basic fields
                - input: {files, evaluator_code, codebase_path*, include_patterns*}
                - result: {initial_score, improvement, summary, output_path*}
                (* codebase-specific fields)
        """
        # Get session from manager (single source of truth)
        session = self.manager.get_session(evolution_id)
        
        if not session:
            return {
                "evolution_id": evolution_id,
                "status": "not_found",
            }
        
        # Check if HTML report exists
        has_html_report = False
        if session.workspace_path:
            html_path = Path(session.workspace_path) / "evolution_report.html"
            has_html_report = html_path.exists()
        
        # Build basic response
        response = {
            "evolution_id": evolution_id,
            "evolution_type": session.evolution_type,  # ✅ New: type indicator
            "status": session.status,
            "iteration": session.current_iter,
            "max_iterations": session.max_iter,
            "best_score": session.best_score,
            "score_history": session.score_history,
            "error": session.error,
            "file_count": len(session.files),  # ✅ New: file count
            "has_html_report": has_html_report,  # ✅ New: HTML report availability
        }
        
        # Calculate improvements
        if session.score_history:
            response["improvements_found"] = len([
                s for i, s in enumerate(session.score_history) 
                if i > 0 and s > session.score_history[i-1]
            ])
        
        # Add config
        response["config"] = {
            "objective": session.objective,
            "iterations": session.max_iter,
            "islands": session.num_islands,
            "model": session.mutator_model,
        }
        
        # Complete mode: include code and result data
        if include_code:
            response["input"] = {
                "evaluator_code": session.evaluator_code,
                "files": session.files,  # ✅ Unified: return all files
            }
            
            # Codebase-specific metadata
            if session.evolution_type == "codebase":
                response["input"]["codebase_path"] = session.codebase_path
                response["input"]["include_patterns"] = session.include_patterns
            
            # Add result data if available
            if session.initial_score is not None:
                response["result"] = {
                    "initial_score": session.initial_score,
                    "improvement": session.improvement,
                    "summary": session.summary,
                }
                
                # Codebase-specific result
                if session.evolution_type == "codebase":
                    response["result"]["output_path"] = session.output_path
        
        return response
    
    @tool
    async def cancel_evolution(
        self,
        evolution_id: str,
    ) -> Dict[str, Any]:
        """
        Cancel a running evolution.

        Args:
            evolution_id: Evolution ID to cancel

        Returns:
            dict: Result with success status
        """
        session = self.manager.get_session(evolution_id)
        if not session:
            return {
                "success": False,
                "error": f"Evolution {evolution_id} not found",
            }
        
        if session.task and not session.task.done():
            session.task.cancel()
            session.status = "cancelled"
            return {
                "success": True,
                "evolution_id": evolution_id,
                "message": "Evolution cancelled",
            }
        else:
            return {
                "success": False,
                "error": "Evolution not running or already finished",
                "status": session.status,
            }
    
    @tool(exclude=True)
    async def list_evolutions(
        self,
        status: Optional[str] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        List evolution sessions.

        Args:
            status: Optional status filter ("running", "completed",  "failed")
            limit: Maximum number of results

        Returns:
            dict: List of evolution sessions
        """
        sessions = self.manager.list_sessions(status_filter=status, limit=limit)
        
        evolutions = []
        for s in sessions:
            evolutions.append({
                "evolution_id": s.evolution_id,
                "evolution_type": s.evolution_type,  # ✅ New: type indicator
                "status": s.status,
                "objective": s.objective,
                "iteration": s.current_iter,
                "max_iterations": s.max_iter,
                "best_score": s.best_score,
                "initial_score": s.initial_score,
                "improvement": s.improvement,
                "file_count": len(s.files),  # ✅ New: file count
                "islands": s.num_islands,
                "model": s.mutator_model,
                "created_at": s.created_at,
                "started_at": s.started_at,
                "completed_at": s.completed_at,
            })
        
        return {
            "success": True,
            "evolutions": evolutions,
            "total": len(evolutions),
        }
    
    @tool(exclude=True)
    async def get_evolution_html_report(
        self,
        evolution_id: str,
    ) -> Dict[str, Any]:
        """
        Get HTML visualization report of evolution
        
        Args:
            evolution_id: Evolution ID
        
        Returns:
            {
                "success": bool,
                "html": str,  # HTML content (if successful)
                "error": str  # Error message (if failed)
            }
        """
        session = self.manager.get_session(evolution_id)
        
        if not session:
            return {
                "success": False,
                "error": f"Evolution {evolution_id} not found"
            }
        
        if not session.workspace_path:
            return {
                "success": False,
                "error": "Evolution workspace not available"
            }
        
        html_path = Path(session.workspace_path) / "evolution_report.html"
        
        if not html_path.exists():
            return {
                "success": False,
                "error": "HTML report not found. Evolution may not be completed yet."
            }
        
        try:
            html_content = html_path.read_text(encoding='utf-8')
            return {
                "success": True,
                "html": html_content
            }
        except Exception as e:
            logger.error(f"Failed to read HTML report: {e}")
            return {
                "success": False,
                "error": f"Failed to read HTML report: {str(e)}"
            }
