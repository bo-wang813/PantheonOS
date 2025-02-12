import asyncio
from pantheon.agent import Agent
from pantheon.team import SequentialTeam


thinking_agent = Agent(
    name="thinking_agent",
    instructions="You are a thinking agent. You like to think about the problem.",
    model="deepseek/deepseek-reasoner",
)

action_agent = Agent(
    name="action_agent",
    instructions="You are a action agent. You like to take action to solve the problem.",
    model="gpt-4o-mini"
)

team = SequentialTeam(
    [thinking_agent, action_agent],
    connect_prompt="Now take actions or give the final answer.",
)

async def main():
    resp = await team.run("How many 'r's in 'strawberry'?", response_format=int)
    print(resp.content)

asyncio.run(main())
