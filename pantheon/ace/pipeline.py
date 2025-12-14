"""
ACE Learning Pipeline module for Pantheon.

The pipeline manages the asynchronous learning workflow:
1. Receives LearningInput from agents
2. Runs Reflector analysis
3. Runs SkillManager to decide updates
4. Applies updates to Skillbook
"""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from ..utils.log import logger
from .reflector import Reflector
from .skill_manager import SkillManager, UpdateOperation
from .skillbook import Skillbook


# ===========================================================================
# LearningInput - Data structure for learning submissions
# ===========================================================================


@dataclass
class LearningInput:
    """Data submitted to the Reflector for analysis."""

    turn_id: str
    agent_name: str
    question: str  # User's question or delegation instruction
    trajectory: str  # Formatted conversation trajectory (truncated)
    final_answer: str  # Agent's final response
    skill_ids_cited: List[str] = field(default_factory=list)  # Skills referenced
    details_path: str = ""  # Path to full untruncated details


def build_learning_input(
    turn_id: str,
    agent_name: str,
    messages: List[dict],
    learning_dir: str = ".pantheon/ace/learning",
    max_arg_length: int = 200,
) -> LearningInput:
    """
    Build a LearningInput from conversation messages.
    
    Args:
        turn_id: Unique identifier for this turn
        agent_name: Name of the agent
        messages: List of message dicts from the conversation
        learning_dir: Directory to save full turn details
        max_arg_length: Max chars for tool args/results in trajectory
    
    Returns:
        LearningInput ready for submission to Reflector
    """
    # 1. Extract user question (first user message)
    question = ""
    for msg in messages:
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, str):
                question = content
            elif isinstance(content, list):
                # Handle multimodal content
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        question = item.get("text", "")
                        break
            break

    # 2. Format trajectory with truncation
    trajectory_parts: List[str] = []
    final_answer = ""
    skill_ids: List[str] = []

    for msg in messages:
        role = msg.get("role", "")
        
        # Prioritize _llm_content if present and not empty
        # This captures the actual context sent to the LLM (e.g. XML wrappers)
        # We check truthiness to allow fallback if _llm_content is accidentally empty
        if msg.get("_llm_content"):
            content = msg["_llm_content"]
        else:
            content = msg.get("content")
            
        content = content or ""

        # Handle multimodal content
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            content = " ".join(text_parts)

        if role == "user":
            trajectory_parts.append(f"[USER]\n{content}")

        elif role == "assistant":
            # Extract cited skill IDs (format: [xxx-00001])
            if content:
                skill_ids.extend(re.findall(r"\[([a-z]+-\d{5})\]", content))

            tool_calls = msg.get("tool_calls")
            if tool_calls:
                # Assistant with tool calls
                if content:
                    trajectory_parts.append(f"[ASSISTANT]\n{content}")
                for tc in tool_calls:
                    func = tc.get("function", {})
                    name = func.get("name", "unknown")
                    args = func.get("arguments", "")
                    tc_id = tc.get("id", "")

                    # Truncate args
                    if len(args) > max_arg_length:
                        args = args[:max_arg_length] + "... (truncated)"

                    trajectory_parts.append(
                        f"[TOOL_CALL: {name}] id={tc_id}\n{args}"
                    )
            else:
                # Final assistant response
                trajectory_parts.append(f"[ASSISTANT]\n{content}")
                final_answer = content

        elif role == "tool":
            tc_id = msg.get("tool_call_id", "")
            result = content

            # Truncate result
            if len(result) > max_arg_length:
                result = result[:max_arg_length] + "... (truncated)"

            trajectory_parts.append(f"[TOOL_RESULT] id={tc_id}\n{result}")

    # 3. Save full details for later reference
    details_path = ""
    if learning_dir:
        try:
            details_path_obj = Path(learning_dir) / f"turn_{turn_id}.json"
            details_path_obj.parent.mkdir(parents=True, exist_ok=True)
            with details_path_obj.open("w", encoding="utf-8") as f:
                json.dump(
                    {
                        "turn_id": turn_id,
                        "agent_name": agent_name,
                        "messages": messages,
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
            details_path = str(details_path_obj)
        except Exception as e:
            logger.warning(f"Failed to save turn details: {e}")

    return LearningInput(
        turn_id=turn_id,
        agent_name=agent_name,
        question=question,
        trajectory="\n\n".join(trajectory_parts),
        final_answer=final_answer,
        skill_ids_cited=list(set(skill_ids)),
        details_path=details_path,
    )


# ===========================================================================
# ACELearningPipeline - Async learning workflow
# ===========================================================================


class ACELearningPipeline:
    """
    Asynchronous learning pipeline for ACE.
    
    Uses asyncio.Queue for thread-safe processing of learning tasks.
    Learning happens in the background without blocking user interactions.
    """

    # Minimum trajectory length to consider for learning
    MIN_TRAJECTORY_LENGTH = 50

    def __init__(
        self,
        skillbook: Skillbook,
        reflector: Reflector,
        skill_manager: SkillManager,
        learning_dir: str,
        cleanup_after_learning: bool = False,
    ):
        self._skillbook = skillbook
        self._reflector = reflector
        self._skill_manager = skill_manager
        self._learning_dir = learning_dir
        self._cleanup_after_learning = cleanup_after_learning
        self._queue: asyncio.Queue[LearningInput] = asyncio.Queue()
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Start the background learning task."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._process_loop())
        logger.info("ACE learning pipeline started")

    async def stop(self) -> None:
        """Stop the pipeline and save skillbook."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        # Final save
        self._skillbook.save()
        logger.info("ACE learning pipeline stopped")

    def submit(self, input: LearningInput) -> None:
        """
        Submit a learning task (non-blocking).
        
        Will skip if the input doesn't meet learning criteria.
        """
        if self._should_skip(input):
            logger.debug(f"Skipping learning for {input.agent_name}: criteria not met")
            return
        self._queue.put_nowait(input)
        logger.debug(f"Submitted learning task for {input.agent_name}")

    def _should_skip(self, input: LearningInput) -> bool:
        """Check if this input should be skipped."""
        # Empty trajectory
        if not input.trajectory or len(input.trajectory) < self.MIN_TRAJECTORY_LENGTH:
            return True
        # No question
        if not input.question:
            return True
        return False

    async def _process_loop(self) -> None:
        """Background loop processing learning tasks."""
        while self._running:
            try:
                input = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._process_task(input)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Learning pipeline loop error: {e}")

    async def _process_task(self, input: LearningInput) -> None:
        """Process a single learning task."""
        try:
            logger.debug(f"Processing learning for {input.agent_name}")

            # 1. Reflector analysis
            reflection = await self._reflector.reflect(input, self._skillbook)
            
            if reflection.confidence < 0.3:
                logger.debug(f"Low confidence reflection ({reflection.confidence}), skipping")
                return

            # 2. Apply skill tags immediately
            for tag in reflection.skill_tags:
                skill = self._skillbook.tag_skill(tag.id, tag.tag)
                if skill:
                    logger.debug(f"Tagged skill {tag.id} as {tag.tag}")

            # 3. Get update operations from SkillManager
            operations = await self._skill_manager.update_skills(
                reflection, self._skillbook, input.agent_name
            )

            # 4. Apply operations and collect stats
            ops_summary = {"ADD": 0, "UPDATE": 0, "TAG": 0, "REMOVE": 0}
            for op in operations:
                self._apply_operation(op)
                ops_summary[op.type] = ops_summary.get(op.type, 0) + 1

            # 5. Persist after each update
            self._skillbook.save()
            
            # 6. Cleanup trajectory file if configured
            if self._cleanup_after_learning and input.details_path:
                self._cleanup_learning_file(input.details_path)
            
            # 7. Log learning summary
            ops_str = ", ".join(f"{k}:{v}" for k, v in ops_summary.items() if v > 0) or "none"
            logger.info(
                f"📚 [ACE Learning] Agent: {input.agent_name} | "
                f"Tags: {len(reflection.skill_tags)} | Ops: [{ops_str}] | "
                f"Confidence: {reflection.confidence:.2f}"
            )
            logger.info(f"📊 [ACE Stats] {self._skillbook.summary_line()}")

        except Exception as e:
            logger.error(f"Learning task failed for {input.agent_name}: {e}")
            # Don't re-raise - continue processing next task

    def _cleanup_learning_file(self, file_path: str) -> None:
        """Delete a learning trajectory file after processing."""
        try:
            import os
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Cleaned up learning file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup learning file {file_path}: {e}")

    def _apply_operation(self, op: UpdateOperation) -> None:
        """Apply a single update operation to the skillbook."""
        try:
            if op.type == "ADD":
                if op.section and op.content:
                    skill = self._skillbook.add_skill(
                        section=op.section,
                        content=op.content,
                        agent_scope=op.agent_scope or "global",
                    )
                    if skill:
                        logger.info(f"Added skill: {skill.id}")

            elif op.type == "UPDATE":
                if op.skill_id and op.content:
                    skill = self._skillbook.update_skill(op.skill_id, content=op.content)
                    if skill:
                        logger.info(f"Updated skill: {skill.id}")

            elif op.type == "TAG":
                if op.skill_id:
                    # Apply tags from individual fields
                    if op.helpful:
                        self._skillbook.tag_skill(op.skill_id, "helpful", op.helpful)
                        logger.debug(f"Tagged skill {op.skill_id}: helpful+{op.helpful}")
                    if op.harmful:
                        self._skillbook.tag_skill(op.skill_id, "harmful", op.harmful)
                        logger.debug(f"Tagged skill {op.skill_id}: harmful+{op.harmful}")
                    if op.neutral:
                        self._skillbook.tag_skill(op.skill_id, "neutral", op.neutral)
                        logger.debug(f"Tagged skill {op.skill_id}: neutral+{op.neutral}")

            elif op.type == "REMOVE":
                if op.skill_id:
                    self._skillbook.remove_skill(op.skill_id, soft=True)
                    logger.info(f"Removed skill: {op.skill_id}")

        except Exception as e:
            logger.error(f"Failed to apply operation {op.type}: {e}")
