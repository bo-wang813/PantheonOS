"""
ACE (Agentic Context Engineering) module for Pantheon.

This module provides a long-term memory system that allows agents to learn
from their interactions and improve over time.

Core Components:
- Skillbook: Structured knowledge store with skills organized by section
- Reflector: Analyzes agent trajectories to extract learnings
- SkillManager: Decides what updates to apply to the Skillbook
- ACELearningPipeline: Async pipeline coordinating the learning process
"""

from typing import Optional, Tuple

from .pipeline import ACELearningPipeline, LearningInput, build_learning_input
from .reflector import (
    ExtractedLearning,
    Reflector,
    ReflectorOutput,
    SkillTag,
)
from .skill_manager import SkillManager, SkillManagerOutput, UpdateOperation
from .skillbook import Skill, Skillbook


def create_ace_resources(
    enable: Optional[bool] = None,
    config: Optional[dict] = None,
) -> Tuple[Optional[Skillbook], Optional[ACELearningPipeline]]:
    """
    Factory function to create ACE resources.
    
    Reads configuration from settings if not provided.
    Returns (None, None) if ACE is disabled.
    
    Args:
        enable: Override for enable flag (None = use config)
        config: Override for ACE config (None = read from settings)
    
    Returns:
        Tuple of (Skillbook, ACELearningPipeline) or (None, None)
    """
    from ..settings import get_settings
    from ..utils.log import logger
    
    settings = get_settings()
    _config = config or settings.get_ace_config()
    _enable = enable if enable is not None else _config["enable"]
    
    if not _enable:
        logger.info("ACE disabled")
        return None, None
    
    skillbook = Skillbook(
        max_skills_per_section=_config["max_skills_per_section"],
        max_content_length=_config["max_content_length"],
        enable_agent_scope=_config.get("enable_agent_scope", False),
    )
    skillbook.load(_config["skillbook_path"])
    
    pipeline = ACELearningPipeline(
        skillbook=skillbook,
        reflector=Reflector(model=_config["learning_model"]),
        skill_manager=SkillManager(model=_config["learning_model"]),
        learning_dir=_config["learning_dir"],
        cleanup_after_learning=_config.get("cleanup_after_learning", False),
    )
    
    logger.info(f"ACE enabled: {len(skillbook.skills())} skills loaded")
    return skillbook, pipeline


__all__ = [
    # Factory
    "create_ace_resources",
    # Skillbook
    "Skill",
    "Skillbook",
    # Learning
    "LearningInput",
    "build_learning_input",
    # Reflector
    "Reflector",
    "ReflectorOutput",
    "SkillTag",
    "ExtractedLearning",
    # SkillManager
    "SkillManager",
    "SkillManagerOutput",
    "UpdateOperation",
    # Pipeline
    "ACELearningPipeline",
    # Prompt Constants
    "SKILLBOOK_USAGE_INSTRUCTIONS",
    "SKILLBOOK_HEADER",
    "USER_RULES_HEADER",
]

# Import prompt constants from skillbook
from .skillbook import (
    SKILLBOOK_USAGE_INSTRUCTIONS,
    SKILLBOOK_HEADER,
    USER_RULES_HEADER,
)
