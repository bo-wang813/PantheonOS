import asyncio

from pantheon.agent import Agent
from pantheon.team import SwarmTeam
from pantheon.repl.team import Repl


async def main():
    scifi_fan = Agent(
        name="Scifi Fan",
        instructions="You are a scifi fan.",
        model="gpt-4o-mini",
    )

    romance_fan = Agent(
        name="Romance Fan",
        instructions="You are a romance fan.",
        model="gpt-4o-mini",
    )
    
    @scifi_fan.tool
    def transfer_to_romance_fan():
        return romance_fan
    
    @romance_fan.tool
    def transfer_to_scifi_fan():
        return scifi_fan

    team = SwarmTeam([scifi_fan, romance_fan])
    repl = Repl(team)
    await repl.run()


if __name__ == "__main__":
    asyncio.run(main())
