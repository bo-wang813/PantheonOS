import asyncio
from pantheon.agent import Agent
from pantheon.team import SequentialTeam


scifi_fan = Agent(
    name="scifi_fan",
    instructions="You are a scifi fan. You like to read scifi books.",
)
romance_fan = Agent(
    name="romance_fan",
    instructions="You are a romance fan. You like to read romance books.",
)

team = SequentialTeam([scifi_fan, romance_fan])

asyncio.run(team.chat("Recommand me some books."))
