"""
Test script for gene panel selection workflow.
Uses the factory system to create the single_cell_team and run a gene panel selection task.
"""
import os
import sys
import asyncio
import loguru

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from pantheon.endpoint import Endpoint
from pantheon.factory import create_team_from_template
from pantheon.utils.display import print_agent_message


PROMPT = """
# Task : A human immune oncology gene profiling panel
Plex: 1000 genes with annotation, with genes grouped in major categories
Purpose: the gene panel should have the ability to catalog all cell types, enable immune profiling of the tumor microenvironment and characterize the cell states based on cytokine and cancer signaling pathways. Specifically, the panel should be able to resolve immune cells types, profile key cancer signaling pathways, analyze cell state based on key cytokine profile, understand if a cell is exhausted or not, and distinguish different cancer cell stages based on its expression of different oncogenes or signaling molecules, so that an end user can characterize the tumor microenvironment and explore cancer signaling pathways, etc.

- **adata_path:** `/home/erwinpi/pantheon-agents/test_gps/immune_10k.h5ad`
- **Dataset source:** bioRxiv Preprint (2024) — DOI: 10.1101/2024.01.17.576110
"""


async def main():
    loguru.logger.remove()
    loguru.logger.add(sys.stdout, level="INFO")

    workdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workdir")
    os.makedirs(workdir, exist_ok=True)

    # Start endpoint
    endpoint = Endpoint(
        config=None,
        workspace_path=os.path.dirname(os.path.abspath(__file__)),
    )
    asyncio.create_task(endpoint.run(remote=False))

    # Wait for endpoint to be ready
    for _ in range(100):
        if endpoint._setup_completed:
            break
        await asyncio.sleep(0.2)

    if not endpoint._setup_completed:
        print("ERROR: Endpoint failed to start within timeout")
        return

    print("Endpoint ready. Creating team...")

    # Create team from template
    team = await create_team_from_template(
        endpoint,
        template_id="single_cell_team",
        learning_config=None,
        check_toolsets=True,
        enable_mcp=True,
    )

    print(f"Team created with {len(team.agents)} agents")
    for agent in team.agents:
        name = agent.name if hasattr(agent, 'name') else str(agent)
        print(f"  - {name}")

    # Run with gene panel selection prompt
    full_prompt = PROMPT + f"\n\nWorkdir: {workdir}"

    def process_step_message(msg: dict):
        agent_name = msg.get("agent_name", "Agent?")
        try:
            print_agent_message(agent_name, msg)
        except Exception:
            print(f"{agent_name}:\n", msg)

    print("\n" + "=" * 80)
    print("STARTING GENE PANEL SELECTION TASK")
    print("=" * 80 + "\n")

    await team.run(full_prompt, process_step_message=process_step_message)

    print("\n" + "=" * 80)
    print("TASK COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
