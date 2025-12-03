import re
import time
import uuid

from ..agent import (
    Agent,
    AgentInput,
    AgentTransfer,
    RemoteAgent,
    get_current_run_context,
)
from ..constant import SystemPromptMode
from ..memory import Memory
from ..utils.log import logger
from ..utils.misc import run_func
from .base import Team


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug or "agent"


def _build_execution_context_id(
    parent_metadata: dict,
    run_context,
    depth: int,
    target_name: str,
) -> str:
    """Return ID formatted as '<root>|d<depth>|<agent>|<rand4>'.

    - root: derived from parent's execution_context_id or caller memory id
    - depth: current delegation depth
    - agent: safe version of the child agent name
    - rand4: short random suffix to keep IDs unique even for parallel calls
    """

    def _extract_root_token() -> str:
        execution_context_id = parent_metadata.get("execution_context_id")
        if execution_context_id and "|" in execution_context_id:
            return execution_context_id.split("|", 1)[0]

        memory = getattr(run_context, "memory", None)
        memory_id = getattr(memory, "id", "memory")
        mem_prefix = str(memory_id)[:8] if memory_id else "memory"
        return f"{mem_prefix}-{uuid.uuid4().hex[:6]}"

    root_token = _extract_root_token()

    return "|".join(
        [
            root_token,
            f"d{depth}",
            _slugify(target_name),
            uuid.uuid4().hex[:4],
        ]
    )


def _build_child_context_metadata(
    run_context,
    target_agent: Agent,
    context_variables: dict,
    max_depth: int = 5,
) -> dict:
    if run_context is None:
        raise RuntimeError(
            "call_agent must be executed within an active agent tool call"
        )
    parent_metadata = context_variables.get("_metadata") or {}
    parent_path = parent_metadata.get("chain_path")
    if parent_path:
        chain_path = list(parent_path)
    else:
        chain_path = [run_context.agent.name]
    if target_agent.name in chain_path:
        raise RuntimeError(
            "Delegation loop detected: this agent already appears in the current chain."
        )
    chain_path.append(target_agent.name)

    child_depth = max(len(chain_path) - 1, 0)
    if child_depth > max_depth:
        raise RuntimeError("Delegation depth limit reached.")

    execution_context_id = _build_execution_context_id(
        parent_metadata, run_context, child_depth, target_agent.name
    )

    tool_call_id = context_variables.get("tool_call_id") or (
        "call_" + uuid.uuid4().hex[:12]
    )

    metadata = {
        "execution_context_id": execution_context_id,
        "chain_path": chain_path,
        "parent": {
            "agent": run_context.agent.name,
            "call_id": tool_call_id,
        },
    }

    return metadata


class PantheonTeam(Team):
    """Pantheon team structure with unified agent architecture.

    All agents are treated equally with the same capabilities:
    - list_agents(): Discover other agents in the team
    - call_agent(): Delegate tasks to other agents
    - transfer_to_agent(): Hand off control to another agent

    Features enabled when team has multiple agents (len > 1).
    """

    def __init__(
        self,
        agents: list[Agent | RemoteAgent],
        use_summary: bool = False,
        max_delegate_depth: int | None = 5,
        allow_transfer: bool = True,
    ):
        """Initialize PantheonTeam with unified agent architecture.

        Args:
            agents: List of agents in the team.
            use_summary: If True, generate and prepend context summary
                         when delegating tasks.
            max_delegate_depth: Maximum depth for nested call_agent calls.
            allow_transfer: If True, add transfer_to_agent tool to agents.

        Note:
            All agents are equal - the first one is used as the default
            entry point but receives no special treatment.
        """
        if not agents:
            raise ValueError("Team must have at least one agent")

        self.team_agents = agents
        self.use_summary = use_summary
        self.max_delegate_depth = max_delegate_depth
        self.allow_transfer = allow_transfer

        super().__init__(agents)

        # All agents have the same capabilities
        for agent in self.team_agents:
            if isinstance(agent, Agent):
                agent.system_prompt_mode = SystemPromptMode.FULL
                agent.can_delegate = True

        # Keep triage reference for backward compatibility (first agent)
        self.triage = self.team_agents[0]

    def get_active_agent(self, memory: Memory) -> Agent | RemoteAgent:
        active_agent_name = memory.extra_data.get("active_agent")
        if (active_agent_name is None) or (active_agent_name not in self.agents):
            active_agent_name = list(self.agents.keys())[0]
            logger.debug(
                f"Active agent not found in memory, setting to {active_agent_name}"
            )
            memory.extra_data["active_agent"] = active_agent_name
        active_agent = self.agents[active_agent_name]
        return active_agent

    def set_active_agent(self, memory: Memory, agent_name: str):
        memory.extra_data["active_agent"] = agent_name

    async def add_list_agents_tool(self):
        """Add list_agents() tool to all agents."""

        def get_agents_info(exclude_slug: str | None = None) -> list[dict]:
            """Get info for all agents except the one with exclude_slug."""
            agents_info = []
            for agent_name, agent in self.agents.items():
                slug = _slugify(agent_name)
                if slug == exclude_slug:
                    continue
                info = {"name": slug}
                if hasattr(agent, "description") and agent.description:
                    info["description"] = agent.description
                agents_info.append(info)
            return agents_info

        for agent in self.team_agents:
            caller_slug = _slugify(agent.name)

            def make_list_agents(exclude: str):
                """Create list_agents function with caller excluded."""

                def list_agents():
                    """List all available agents and their capabilities."""
                    agents_info = get_agents_info(exclude_slug=exclude)
                    if not agents_info:
                        return "No other agents available."

                    output = "**Available Agents:**\n\n"
                    for info in agents_info:
                        output += f"- **{info['name']}**"
                        if "description" in info:
                            output += f": {info['description']}"
                        output += "\n"

                    return output

                return list_agents

            list_agents_func = make_list_agents(caller_slug)
            list_agents_func.__name__ = "list_agents"
            list_agents_func.__doc__ = (
                "List all available agents and their capabilities. "
                "Use this to discover agents you can delegate to via call_agent() "
                "or transfer control to via transfer_to_agent()."
            )

            await run_func(agent.tool, list_agents_func)

    async def add_unified_call_agent_tool(self):
        """Add unified call_agent(agent_name, instruction) tool for agents."""

        async def _add_call_agent_tool_to_agent(
            calling_agent: Agent | RemoteAgent,
        ):
            """Add call_agent() tool to an agent."""

            async def call_agent(
                agent_name: str,
                instruction: str,
                context_variables: dict | None = None,
            ):
                """Delegate a task to another agent in the team.

                Args:
                    agent_name: Name of the target agent to delegate to.
                    instruction: Clear task description for the target agent.

                Returns:
                    Response content produced by the target agent.
                """
                target_agent = self.get_target_agent(agent_name, instruction)
                run_context = get_current_run_context()

                context_variables = dict(context_variables or {})
                child_metadata = _build_child_context_metadata(
                    run_context,
                    target_agent,
                    context_variables,
                    self.max_delegate_depth,
                )
                execution_context_id = child_metadata["execution_context_id"]

                child_context_variables = dict(context_variables)
                child_context_variables["_metadata"] = child_metadata

                # Build task message with optional history summary
                task_message = await create_delegation_task_message(
                    history=run_context.memory.get_messages(None)
                    if run_context.memory
                    else [],
                    instruction=instruction,
                    use_summary=self.use_summary,
                )
                if not task_message:
                    return ""

                parent_step_hook = run_context.process_step_message
                parent_chunk_hook = run_context.process_chunk

                async def wrapped_step(step_message: dict):
                    metadata = step_message.get("_metadata")
                    if not metadata or "execution_context_id" not in metadata:
                        step_message["_metadata"] = child_metadata
                    if parent_step_hook is not None:
                        await run_func(parent_step_hook, step_message)

                async def wrapped_chunk(chunk: dict):
                    metadata = chunk.get("_metadata")
                    if not metadata or "execution_context_id" not in metadata:
                        chunk["_metadata"] = child_metadata
                    if parent_chunk_hook is not None:
                        await run_func(parent_chunk_hook, chunk)

                child_memory = Memory(
                    name=f"{target_agent.name}-{execution_context_id}"
                )
                response = await target_agent.run(
                    task_message,
                    memory=child_memory,
                    use_memory=False,
                    update_memory=False,
                    process_step_message=wrapped_step,
                    process_chunk=wrapped_chunk,
                    execution_context_id=execution_context_id,
                    context_variables=child_context_variables,
                    allow_transfer=False,
                )

                content = response.content if response else ""
                return content

            call_agent.__name__ = "call_agent"
            call_agent.__doc__ = (
                "Delegate a task to another agent in the team. "
                "Pass the agent_name and a clear instruction describing the "
                "context, what to do, and the desired output."
            )

            await run_func(calling_agent.tool, call_agent)

        for agent in self.team_agents:
            await _add_call_agent_tool_to_agent(agent)

    async def add_transfer_tools_to_agents(self):
        """Add transfer tool to all agents for inter-agent communication."""

        def make_transfer_func(source_name: str):
            """Create a transfer function with source agent name captured."""

            def transfer_to_agent(target_name: str):
                """Transfer control to another agent by name.

                Args:
                    target_name: Name of the agent to transfer to.
                """
                # Normalize target_name to match agent lookup
                normalized = target_name.replace(" ", "_").lower()
                agent_map = {
                    aname.replace(" ", "_").lower(): agent
                    for aname, agent in self.agents.items()
                }
                if normalized not in agent_map:
                    raise ValueError(f"Unknown agent: {target_name}")
                if normalized == source_name.replace(" ", "_").lower():
                    raise ValueError("Cannot transfer to self")
                return agent_map[normalized]

            return transfer_to_agent

        for source_agent in self.team_agents:
            transfer_func = make_transfer_func(source_agent.name)
            await run_func(source_agent.tool, transfer_func)

    async def async_setup(self):
        """Setup team by enabling inter-agent tools when multiple agents exist.

        Tools added when len(agents) > 1:
        - transfer_to_agent(): Transfer control to another agent (if allow_transfer)
        - list_agents(): Discover other agents in the team
        - call_agent(): Delegate tasks to other agents
        """
        if len(self.team_agents) > 1:
            if self.allow_transfer:
                await self.add_transfer_tools_to_agents()
            await self.add_list_agents_tool()
            await self.add_unified_call_agent_tool()

    async def run(self, msg: AgentInput, memory: Memory | None = None, **kwargs):
        await self.async_setup()
        if memory is None:
            memory = Memory(name="pantheon-team")
        while True:
            active_agent = self.get_active_agent(memory)
            resp = await active_agent.run(msg, memory=memory, **kwargs)
            if isinstance(resp, AgentTransfer):
                transfer_call_id = resp.tool_call_id
                logger.info(
                    f"[TRANSFER] {active_agent.name} -> {resp.to_agent} | tool_call_id: {transfer_call_id}"
                )
                tool_message = {
                    "role": "tool",
                    "tool_call_id": transfer_call_id
                    or ("call_" + str(uuid.uuid4())[:20]),
                    "tool_name": "transfer",
                    "content": resp.to_agent,
                }
                # Switch to target agent and continue loop with tool_message
                self.set_active_agent(memory, resp.to_agent)
                msg = tool_message
            else:
                return resp

    def get_target_agent(self, agent_name: str, instruction: str) -> Agent:
        """Get target agent by name for delegation.

        Args:
            agent_name: Name of the target agent (supports slug format).
            instruction: Task instruction (must not be empty).

        Returns:
            The target Agent instance.
        """
        # Normalize agent name (e.g., "Data Analyst" -> "data_analyst")
        all_agents = {
            aname.replace(" ", "_").lower(): agent
            for aname, agent in self.agents.items()
        }
        agent_name = agent_name.replace(" ", "_").lower()

        if agent_name not in all_agents:
            raise ValueError(
                f"Agent '{agent_name}' not found. "
                f"Available: {list(all_agents.keys())}"
            )

        if not instruction or not instruction.strip():
            raise ValueError("Instruction cannot be empty")

        target_agent = all_agents[agent_name]
        if not isinstance(target_agent, Agent):
            raise NotImplementedError(
                "call_agent currently supports only local Agent instances"
            )
        return target_agent


async def create_delegation_task_message(
    history: list[dict],
    instruction: str,
    use_summary: bool = True,
) -> str | None:
    """Create a delegated task message with optional summary context."""
    if not instruction:
        return None

    # If summary is disabled, the instruction is the entire content.
    if not use_summary:
        return instruction

    # Default behavior: Summarize history and append the instruction.
    summary_text = None
    if history:
        try:
            from ..chatroom.special_agents import get_summary_generator

            summary_gen = get_summary_generator()
            summary_text = await summary_gen.generate_summary(history, max_tokens=1000)
        except Exception as e:
            logger.warning(f"Failed to generate summary for delegation: {e}")

    content_parts = []
    if summary_text:
        content_parts.append(f"Context Summary:\n{summary_text}")
    content_parts.append(f"Task: {instruction}")
    return "\n\n".join(content_parts)
