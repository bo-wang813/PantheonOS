"""Ephemeral message generator for Modal Workflow System."""
import os
from .task_state import ConversationState, ArtifactRoles

ARTIFACT_REMINDER_HAS_ARTIFACTS = """<artifact_reminder>
You have created the following artifacts:
{artifacts}
CRITICAL REMINDER: artifacts should be AS CONCISE AS POSSIBLE.
</artifact_reminder>"""

ARTIFACT_REMINDER_NO_ARTIFACTS = """<artifact_reminder>
You have not yet created any artifacts.
Artifacts should be written to: {brain_dir}
</artifact_reminder>"""

ACTIVE_TASK_REMINDER = """<active_task_reminder>
Current task: task_name:"{task_name}" mode:{ctx_mode}
task_status:"{task_status}" task_summary:"{task_summary}"
Tools since last update: {tools_since_update}
YOUR CURRENT MODE IS: {ctx_mode}. Embody this mindset.
REMEMBER: user WILL NOT SEE your messages. Use notify_user to communicate.
</active_task_reminder>"""

NO_ACTIVE_TASK_REMINDER = """<no_active_task_reminder>
You are not in a task because: {reason}
For simple requests (explaining code, single-file edits), no task is needed.
For complex work, create task.md first, then call task_boundary.
Do NOT call notify_user unless requesting file review.
</no_active_task_reminder>"""

PLAN_ARTIFACT_MODIFIED_REMINDER = """<plan_artifact_modified_reminder>
You modified plan artifact(s): {files} in {ctx_mode} mode.
Request user review via notify_user before proceeding to execution/analysis.
</plan_artifact_modified_reminder>"""

ARTIFACTS_MODIFIED_REMINDER = """<artifacts_modified_reminder>
You have modified {count} artifact(s) in this task.
Consider updating them as you progress.
</artifacts_modified_reminder>"""

REQUESTED_REVIEW_NOT_IN_TASK_REMINDER = """<requested_review_not_in_task_reminder>
You used notify_user but haven't set task_boundary since.
Either: (1) Enter planning mode to update plan, or (2) Enter execution mode to implement.
</requested_review_not_in_task_reminder>"""

ARTIFACT_FILE_REMINDER = """<artifact_file_reminder>
You have not accessed these files recently:
{files}
</artifact_file_reminder>"""


def generate_ephemeral_message(state: ConversationState, brain_dir: str) -> str:
    """Generate EPHEMERAL_MESSAGE based on current state.
    
    Args:
        state: Current conversation state
        brain_dir: Path to the brain directory for artifacts
        
    Returns:
        XML-formatted ephemeral message content
    """
    parts = []
    
    # 1. artifact_reminder (always included)
    if state.created_artifacts:
        parts.append(ARTIFACT_REMINDER_HAS_ARTIFACTS.format(
            artifacts=chr(10).join(state.created_artifacts)
        ))
    else:
        parts.append(ARTIFACT_REMINDER_NO_ARTIFACTS.format(
            brain_dir=brain_dir
        ))
    
    # 2. Task state reminder (mutually exclusive)
    if state.active_task:
        t = state.active_task
        parts.append(ACTIVE_TASK_REMINDER.format(
            task_name=t.name,
            ctx_mode=t.mode,
            task_status=t.status,
            task_summary=t.summary,
            tools_since_update=state.tools_since_update
        ))
    else:
        parts.append(NO_ACTIVE_TASK_REMINDER.format(
            reason=state.task_boundary_reason
        ))
    
    # 3. Plan artifact modified in plan phase reminder (semantic check)
    if state.active_task and state.active_task.is_plan_phase:
        if state.has_plan_artifacts_modified():
            plan_files = state.get_modified_artifacts_by_role("plan")
            files_str = ", ".join(os.path.basename(p) for p in plan_files)
            parts.append(PLAN_ARTIFACT_MODIFIED_REMINDER.format(
                files=files_str,
                ctx_mode=state.active_task.mode
            ))
    
    # 4. General artifact modification reminder (non-plan phases)
    if state.active_task and not state.active_task.is_plan_phase:
        all_modified = state.get_all_modified_artifacts()
        if all_modified:
            parts.append(ARTIFACTS_MODIFIED_REMINDER.format(
                count=len(all_modified)
            ))
    
    # 5. Pending review reminder (after notify_user, not in task)
    if state.pending_review_paths and not state.active_task:
        parts.append(REQUESTED_REVIEW_NOT_IN_TASK_REMINDER)
    
    # 6. Artifact access reminder (stale artifacts)
    STALE_THRESHOLD = 10
    stale_artifacts = [
        path for path, last_step in state.artifact_last_access.items()
        if state.current_step - last_step > STALE_THRESHOLD
    ]
    if stale_artifacts:
        artifact_lines = [
            f"- {p} (last access: {state.current_step - state.artifact_last_access[p]} steps ago)"
            for p in stale_artifacts
        ]
        parts.append(ARTIFACT_FILE_REMINDER.format(
            files=chr(10).join(artifact_lines)
        ))
    
    return f"<EPHEMERAL_MESSAGE>\n{chr(10).join(parts)}\n</EPHEMERAL_MESSAGE>"
