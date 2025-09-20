"""AI Mega Agents Atlas - Core Framework"""

from .base_agent import BaseAgent, AgentConfig, AgentStatus
from .agent_registry import AgentRegistry
from .revenue_engine import RevenueEngine
from .scaling_manager import ScalingManager

__all__ = [
    "BaseAgent",
    "AgentConfig", 
    "AgentStatus",
    "AgentRegistry",
    "RevenueEngine", 
    "ScalingManager"
]

__version__ = "1.0.0"
__author__ = "AI Mega Agents Atlas Team"
__description__ = "Enterprise-grade AI agent framework for autonomous operation and revenue generation"