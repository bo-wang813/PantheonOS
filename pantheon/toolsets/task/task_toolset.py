"""TaskToolSet for Modal Workflow System.

Provides task_boundary and notify_user tools for managing
workflow modes (PLANNING/EXECUTION/VERIFICATION or RESEARCH/ANALYSIS/INTERPRETATION).
"""
import json
from typing import Optional

from ...toolset import ToolSet, tool
from ...utils.log import logger
from .task_state import ConversationState, ModeSemantics
from .ephemeral import generate_ephemeral_message


class TaskToolSet(ToolSet):
    """Local task toolset - one instance per Agent, state persists across run() calls."""
    
    def __init__(self, name = "task", **kwargs):
        super().__init__(name, **kwargs)
        self.state = ConversationState()
        self._last_task_name: Optional[str] = None
        self._last_mode: Optional[str] = None
        self._last_task_status: Optional[str] = None
        self._last_task_summary: Optional[str] = None
    
    @tool
    async def task_boundary(
        self,
        TaskName: str,
        Mode: str,
        TaskSummary: str,
        TaskStatus: str,
        PredictedTaskSize: int,
        waitForPreviousTools: bool = False
    ) -> dict:
        """
        CRITICAL: You must ALWAYS call this tool as the VERY FIRST tool in your list of tool calls, before any other tools.
        Indicate the start of a task or make an update to the current task. This should roughly correspond to the top-level items in your task.md.
        
        The tool should also be used to update the status and summary periodically throughout the task. When updating the status or summary of the current task, you must use the exact same TaskName as before.
        
        To avoid repeating the same values, use the special string "%SAME%" for Mode, TaskName, TaskStatus, or TaskSummary to reuse the previous value.
        
        Args:
            TaskName: Name of the task boundary. This is the identifier that groups steps together, should be human readable like 'Researching Existing Server Implementation'. This should correspond to a top-level item in task.md.
            Mode: The agent focus to switch to. Common modes: PLANNING/EXECUTION/VERIFICATION (coding) or RESEARCH/ANALYSIS/INTERPRETATION (research).
            TaskSummary: Concise summary of what has been accomplished throughout the entire task so far. Should be at most 1-2 lines, past tense. Cite important files between backticks.
            TaskStatus: Active status of the current action, e.g 'Looking for files'. Should describe what you are GOING TO DO NEXT, not what you have done.
            PredictedTaskSize: Your best estimation on how many tool calls are needed to fulfill this task.
            waitForPreviousTools: If true, wait for all previous tool calls to complete before executing.
        """
        # Handle %SAME% substitution
        task_name = self._last_task_name if TaskName == "%SAME%" else TaskName
        mode = self._last_mode if Mode == "%SAME%" else Mode
        task_summary = self._last_task_summary if TaskSummary == "%SAME%" else TaskSummary
        task_status = self._last_task_status if TaskStatus == "%SAME%" else TaskStatus
        
        # Validate mode: accept known modes, warn for unknown but allow
        if not mode or not mode.strip():
            return {"success": False, "error": "Mode cannot be empty"}
        
        mode_upper = mode.upper()
        if not ModeSemantics.is_known_mode(mode_upper):
            logger.warning(f"Unknown mode '{mode}', proceeding anyway. Known modes: {ModeSemantics.ALL_KNOWN_MODES}")
        
        # Store for next %SAME% reference
        self._last_task_name = task_name
        self._last_mode = mode_upper  # Normalize to uppercase
        self._last_task_summary = task_summary
        self._last_task_status = task_status
        
        self.state.on_task_boundary(task_name, mode_upper, task_status, task_summary)
        return {"success": True, "mode": mode_upper, "task": task_name}
    
    @tool
    async def notify_user(
        self,
        PathsToReview: list[str],
        BlockedOnUser: bool,
        Message: str,
        ConfidenceJustification: str,
        ConfidenceScore: float,
        waitForPreviousTools: bool = True
    ) -> dict:
        """
        This tool is used to communicate with the user.
        
        If you are currently in a task as set by the task_boundary tool, then this is the only way to communicate with the user. Other ways of sending messages while mid-task will not be visible.
        
        When sending messages, be very careful to make this as concise as possible. If requesting review, do not be redundant with the file you are asking to be reviewed.
        IMPORTANT: Format your message in github-style markdown to make your message easier for the USER to parse. 

        CONFIDENCE GRADING: Before setting ConfidenceScore, answer these 6 questions (Yes/No):
        (1) Gaps - any missing parts? (2) Assumptions - any unverified assumptions? (3) Complexity - complex logic with unknowns?
        (4) Risk - non-trivial interactions with bug risk? (5) Ambiguity - unclear requirements forcing design choices? (6) Irreversible - difficult to revert?
        SCORING: 0.8-1.0 = No to ALL questions; 0.5-0.7 = Yes to 1-2 questions; 0.0-0.4 = Yes to 3+ questions.
        
        IMPORTANT: This tool should NEVER be called in parallel with other tools. Execution control will be returned to the user once this tool is called.
        
        Args:
            PathsToReview: List of ABSOLUTE paths to files that the user should be notified about. MUST populate this if requesting review.
            BlockedOnUser: Set to true if you are blocked on user approval to proceed. Set false if just notifying about completion.
            Message: Required message to notify the user with, e.g to provide context or ask questions. Use GitHub Flavored Markdown (GFM) format.
            ConfidenceJustification: Justification for the confidence score. MUST answer the 6 assessment questions with Yes/No.
            ConfidenceScore: Agent's confidence from 0.0-1.0. MUST follow scoring rules above.
            waitForPreviousTools: Should always be True for notify_user to ensure sequential execution.
        """
        self.state.on_notify_user(PathsToReview)
        return {
            "success": True, 
            "interrupt": BlockedOnUser,  # Mimics transfer mechanism
            "message": Message,
            "paths": PathsToReview
        }
    
    def get_ephemeral_prompt(self, context_variables: dict) -> dict:
        """Generate EU message for agent loop to inject before LLM call.
        
        Args:
            context_variables: Agent context variables, should contain 'client_id'
        
        Returns a dict with:
        - content: The EU message content
        - role: "user"
        """
        client_id = context_variables.get("client_id", "default")
        
        # Get brain_dir from settings
        from ...settings import get_settings
        settings = get_settings()
        brain_dir = settings.brain_dir / client_id
        
        # Convert to relative path from workspace (which is pantheon_dir) if possible 
        # or just use absolute path string if that's what generate_ephemeral_message expects
        # generate_ephemeral_message likely needs a string path
        
        eu_content = generate_ephemeral_message(self.state, str(brain_dir))
        
        # Debug logging
        logger.info(f"[TaskToolSet] Generating EU for client_id={client_id}")
        logger.info(f"[TaskToolSet] State: active_task={self.state.active_task}, "
                   f"artifacts={self.state.created_artifacts}, "
                   f"tools_since_boundary={self.state.tools_since_boundary}, "
                   f"current_step={self.state.current_step}")
        logger.info(f"[TaskToolSet] EU Content:\n{eu_content}")
        
        disclaimer = """The following is an <EPHEMERAL_MESSAGE> not actually sent by the user. It is provided by the system as a set of reminders and general important information to pay attention to. Do NOT respond to this message, just act accordingly."""
        return {"role": "user", "content": f"{disclaimer}\n{eu_content}"}
    
    def process_tool_messages(
        self, 
        tool_calls: list[dict], 
        tool_messages: list[dict],
        context_variables: dict
    ):
        """Process tool messages to detect artifact access.
        
        Called by agent after _handle_tool_calls completes.
        Detects file_manager tool calls that access artifact files.
        
        Args:
            tool_calls: Original tool calls from LLM
            tool_messages: Tool response messages
            context_variables: Agent context variables
        """
        client_id = context_variables.get("client_id", "default")
        
        # Get brain_dir from settings
        from ...settings import get_settings
        settings = get_settings()
        brain_dir = str(settings.brain_dir / client_id)
        
        # Update tool counter
        self.state.on_tool_call(len(tool_calls))
        
        # Detect artifact access via file_manager tools
        FILE_TOOLS = ("read_file", "write_file", "update_file", "view_file")
        
        for msg in tool_messages:
            tool_name = msg.get("tool_name", "")
            
            # Check for exact match or provider-prefixed match (e.g. file_manager__write_file)
            is_file_tool = tool_name in FILE_TOOLS or any(
                tool_name.endswith(f"__{t}") for t in FILE_TOOLS
            )
            
            if not is_file_tool:
                continue
            
            # Find corresponding tool call to get file_path argument
            tool_call_id = msg.get("tool_call_id")
            call = next((c for c in tool_calls if c["id"] == tool_call_id), None)
            if not call:
                continue
            
            try:
                args = json.loads(call["function"]["arguments"])
                file_path = args.get("file_path", "")
                
                # Check if path is in brain_dir (artifact file)
                if brain_dir in file_path:
                    self.state.on_artifact_modified(file_path, brain_dir)
                    
                    # Also register as created if new
                    if file_path not in self.state.created_artifacts:
                        self.state.on_artifact_created(file_path)
            except (json.JSONDecodeError, KeyError):
                continue
