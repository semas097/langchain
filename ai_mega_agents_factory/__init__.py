"""
AI Mega Agents Factory - Core Module

This module provides the foundational classes and interfaces for the AI Mega Agents Factory.
All 49 agents inherit from these base classes to ensure consistency and interoperability.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Union
from datetime import datetime
from enum import Enum
import asyncio
import uuid
import json

# Simple replacements for dependencies not available in environment
class BaseModel:
    """Simple BaseModel replacement"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def dict(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

def Field(**kwargs):
    """Simple Field replacement"""
    return kwargs.get('default', None)

class BaseTool:
    """Simple BaseTool replacement"""
    def __init__(self):
        self.name = ""
        self.description = ""


class AgentStatus(str, Enum):
    """Agent execution status"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    COMPLETED = "completed"


class AgentTier(str, Enum):
    """Agent subscription tiers"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class AgentConfig(BaseModel):
    """Base configuration for all agents"""
    agent_id: str = str(uuid.uuid4())
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    tier: AgentTier = AgentTier.FREE
    max_concurrent_tasks: int = 10
    timeout_seconds: int = 300
    enable_metrics: bool = True
    enable_logging: bool = True
    api_key: Optional[str] = None
    webhook_url: Optional[str] = None


class AgentMetrics(BaseModel):
    """Agent performance metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    last_activity: Optional[datetime] = None
    uptime_seconds: int = 0
    
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100


class AgentResult(BaseModel):
    """Standardized agent result"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.metadata is None:
            self.metadata = {}
    execution_time: float = 0.0
    timestamp: datetime = datetime.utcnow()


class BaseAgentFactory(ABC):
    """Base interface for all AI Mega Agents"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.status = AgentStatus.IDLE
        self.metrics = AgentMetrics()
        self._tools: List[BaseTool] = []
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the agent"""
        pass
    
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> AgentResult:
        """Execute a task"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> bool:
        """Cleanup resources"""
        pass
    
    @abstractmethod
    def get_tools(self) -> List[BaseTool]:
        """Get agent-specific tools"""
        pass
    
    async def start(self) -> bool:
        """Start the agent"""
        try:
            if not self._initialized:
                success = await self.initialize()
                if not success:
                    return False
                self._initialized = True
            
            self.status = AgentStatus.RUNNING
            return True
        except Exception as e:
            self.status = AgentStatus.ERROR
            return False
    
    async def stop(self) -> bool:
        """Stop the agent"""
        try:
            success = await self.cleanup()
            self.status = AgentStatus.IDLE
            return success
        except Exception:
            self.status = AgentStatus.ERROR
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status and metrics"""
        return {
            "agent_id": self.config.agent_id,
            "name": self.config.name,
            "status": self.status.value,
            "metrics": self.metrics.dict(),
            "version": self.config.version,
            "tier": self.config.tier.value
        }


class AgentRegistry:
    """Central registry for all agents"""
    
    def __init__(self):
        self._agents: Dict[str, BaseAgentFactory] = {}
        self._agent_types: Dict[str, Type[BaseAgentFactory]] = {}
    
    def register_agent_type(self, name: str, agent_class: Type[BaseAgentFactory]):
        """Register an agent type"""
        self._agent_types[name] = agent_class
    
    async def create_agent(self, agent_type: str, config: AgentConfig) -> Optional[BaseAgentFactory]:
        """Create and register an agent instance"""
        if agent_type not in self._agent_types:
            return None
        
        agent_class = self._agent_types[agent_type]
        agent = agent_class(config)
        
        success = await agent.start()
        if success:
            self._agents[config.agent_id] = agent
            return agent
        return None
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgentFactory]:
        """Get an agent by ID"""
        return self._agents.get(agent_id)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents"""
        return [agent.get_status() for agent in self._agents.values()]
    
    def list_agent_types(self) -> List[str]:
        """List all registered agent types"""
        return list(self._agent_types.keys())
    
    async def stop_agent(self, agent_id: str) -> bool:
        """Stop and remove an agent"""
        agent = self._agents.get(agent_id)
        if agent:
            success = await agent.stop()
            if success:
                del self._agents[agent_id]
            return success
        return False


# Global agent registry instance
agent_registry = AgentRegistry()


class MonetizationService:
    """Service for handling agent monetization"""
    
    def __init__(self):
        self._usage_tracking: Dict[str, Dict[str, int]] = {}
    
    def track_usage(self, agent_id: str, operation: str, count: int = 1):
        """Track usage for billing purposes"""
        if agent_id not in self._usage_tracking:
            self._usage_tracking[agent_id] = {}
        
        if operation not in self._usage_tracking[agent_id]:
            self._usage_tracking[agent_id][operation] = 0
        
        self._usage_tracking[agent_id][operation] += count
    
    def get_usage(self, agent_id: str) -> Dict[str, int]:
        """Get usage statistics for an agent"""
        return self._usage_tracking.get(agent_id, {})
    
    def calculate_cost(self, agent_id: str, tier: AgentTier) -> float:
        """Calculate cost based on usage and tier"""
        usage = self.get_usage(agent_id)
        
        # Pricing model (example)
        pricing = {
            AgentTier.FREE: {"requests": 0.0},
            AgentTier.BASIC: {"requests": 0.01},
            AgentTier.PREMIUM: {"requests": 0.005},
            AgentTier.ENTERPRISE: {"requests": 0.001}
        }
        
        tier_pricing = pricing.get(tier, pricing[AgentTier.FREE])
        total_cost = 0.0
        
        for operation, count in usage.items():
            rate = tier_pricing.get(operation, tier_pricing.get("requests", 0.0))
            total_cost += count * rate
        
        return total_cost


# Global monetization service instance
monetization_service = MonetizationService()

# Import and register agents
def register_all_agents():
    """Register all available agents"""
    try:
        from ai_mega_agents_factory.agents.data_analysis import DataAnalysisAgent
        agent_registry.register_agent_type("data_analysis", DataAnalysisAgent)
    except ImportError:
        pass
        
    try:
        from ai_mega_agents_factory.agents.email import EmailAgent
        agent_registry.register_agent_type("email", EmailAgent)
    except ImportError:
        pass
        
    try:
        from ai_mega_agents_factory.agents.document_processing import DocumentProcessingAgent
        agent_registry.register_agent_type("document_processing", DocumentProcessingAgent)
    except ImportError:
        pass

# Auto-register agents on import
register_all_agents()