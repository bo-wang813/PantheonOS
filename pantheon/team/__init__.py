"""Team module for Pantheon agents framework.

This module provides different team patterns for coordinating multiple agents.
"""

from .base import Team
from .moa import MoATeam
from .sequential import SequentialTeam
from .swarm import SwarmCenterTeam, SwarmTeam
from .aat import AgentAsToolTeam
from .pantheon import PantheonTeam  # Chatroom and Repl use this


__all__ = [
    "Team",
    "SwarmTeam",
    "SwarmCenterTeam",
    "SequentialTeam",
    "MoATeam",
    "AgentAsToolTeam",
    "PantheonTeam",
]
