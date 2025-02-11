import asyncio
from pantheon.agent import Agent
from pantheon.team import MoATeam


biologist = Agent(
    name="biologist",
    instructions="You are a biologist. You will answer the question based on your knowledge of biology.",
)

physicist = Agent(
    name="physicist",
    instructions="You are a physicist. You will answer the question based on your knowledge of physics.",
)

computer_scientist = Agent(
    name="computer_scientist",
    instructions="You are a computer scientist. You will answer the question based on the viewpoint of computer science.",
)

aggregator = Agent(
    name="aggregator",
    instructions="You are a aggregator. You are good at aggregating the information from the experts.",
)

team = MoATeam([biologist, physicist, computer_scientist], aggregator, layers=2)

asyncio.run(team.chat("What is life?"))
