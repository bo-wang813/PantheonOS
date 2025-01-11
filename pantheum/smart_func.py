import asyncio
from typing import Callable
from functools import wraps, partial
import inspect

from funcdesc.parse import parse_func
from funcdesc.pydantic import value_to_field
from pydantic import create_model

from .agent import Agent


def _merge_args(desc, args: tuple, kwargs: dict) -> dict:
    merged = {}
    for i, val in enumerate(desc.inputs):
        if i < len(args):
            merged[val.name] = args[i]
    merged.update(kwargs)
    return merged


def smart_func(
        func: Callable | None = None,
        model: str = "gpt-4o-mini",
        tools: list[Callable] | None = None,
        use_short_term_memory: bool = False,
        short_term_memory: list[dict] | None = None,
    ):
    if func is None:
        return partial(
            smart_func,
            model=model,
            tools=tools,
            use_short_term_memory=use_short_term_memory,
            short_term_memory=short_term_memory,
        )

    desc = parse_func(func)

    fields = {}
    for val in desc.inputs:
        field = value_to_field(val)
        fields[val.name] = (val.type or str, field)

    Input = create_model(
        "Input",
        **fields
    )

    val = desc.outputs[0]
    Response = create_model(
        "Response",
        result=(val.type or str, value_to_field(val))
    )

    agent = Agent(
        name="smart_func",
        instructions=desc.doc,
        model=model,
        tools=tools,
        response_format=Response,
        use_short_term_memory=use_short_term_memory,
        short_term_memory=short_term_memory,
    )

    if inspect.iscoroutinefunction(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            merged = _merge_args(desc, args, kwargs)
            input = Input(**merged)
            response = await agent.run(input)
            return response.content.result
    else:
        @wraps(func)
        def wrapper(*args, **kwargs):
            merged = _merge_args(desc, args, kwargs)
            input = Input(**merged)
            response = asyncio.run(agent.run(input))
            return response.content.result

    return wrapper

