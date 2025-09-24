"""Base Agent Class for AI Mega Agents Atlas

This module provides the foundational base class for all agents in the Atlas.
Each agent inherits from BaseAgent and implements enterprise-grade capabilities
including autonomous operation, revenue generation, auto-scaling, and autonomous
knowledge adaptation.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
import uuid
import json

from .knowledge_adapter import get_knowledge_adapter, AutonomousKnowledgeAdapter


class AgentStatus(Enum):
    """Agent operational status"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    SCALING = "scaling" 
    MAINTENANCE = "maintenance"
    ERROR = "error"
    STOPPED = "stopped"


class RevenueModel(Enum):
    """Available revenue models for agents"""
    SAAS = "saas"
    PAY_PER_USE = "pay_per_use"
    SUBSCRIPTION = "subscription"
    COMMISSION = "commission"
    CONSULTING = "consulting"
    HYBRID = "hybrid"


@dataclass
class AgentConfig:
    """Configuration for agent instance"""
    name: str
    agent_type: str
    version: str = "1.0.0"
    description: str = ""
    revenue_models: List[RevenueModel] = field(default_factory=list)
    scaling_config: Dict[str, Any] = field(default_factory=dict)
    monitoring_config: Dict[str, Any] = field(default_factory=dict)
    security_config: Dict[str, Any] = field(default_factory=dict)
    custom_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMetrics:
    """Agent performance and business metrics"""
    uptime_percentage: float = 0.0
    response_time_ms: float = 0.0
    throughput_per_hour: int = 0
    error_rate: float = 0.0
    revenue_generated: float = 0.0
    active_contracts: int = 0
    resource_utilization: Dict[str, float] = field(default_factory=dict)
    custom_metrics: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Base class for all AI Mega Agents
    
    Provides enterprise-grade capabilities including:
    - Autonomous 24/7 operation
    - Revenue generation and tracking
    - Auto-scaling based on demand
    - Self-healing and error recovery
    - Contract automation
    - Performance monitoring
    - Autonomous knowledge adaptation and learning
    """

    def __init__(self, config: AgentConfig):
        """Initialize the base agent
        
        Args:
            config: Agent configuration object
        """
        self.config = config
        self.agent_id = str(uuid.uuid4())
        self.status = AgentStatus.INITIALIZING
        self.created_at = datetime.utcnow()
        self.last_health_check = None
        self.metrics = AgentMetrics()
        
        # Initialize logging
        self.logger = logging.getLogger(f"mega_agents.{config.agent_type}.{self.agent_id}")
        
        # Initialize internal state
        self._running = False
        self._health_check_interval = 30  # seconds
        self._auto_scale_enabled = True
        
        # Initialize autonomous knowledge adapter
        self.knowledge_adapter = get_knowledge_adapter(config.agent_type)
        self._knowledge_learning_enabled = True
        self._revenue_tracking_enabled = True
        
    async def start(self) -> bool:
        """Start the agent and begin autonomous operation
        
        Returns:
            bool: True if successfully started, False otherwise
        """
        try:
            self.logger.info(f"Starting {self.config.name} agent...")
            
            # Initialize agent-specific components
            await self._initialize()
            
            # Start autonomous knowledge learning
            if self._knowledge_learning_enabled:
                await self.knowledge_adapter.start_autonomous_learning()
            
            # Start health monitoring
            asyncio.create_task(self._health_check_loop())
            
            # Start revenue tracking
            if self._revenue_tracking_enabled:
                asyncio.create_task(self._revenue_tracking_loop())
                
            # Start auto-scaling monitoring
            if self._auto_scale_enabled:
                asyncio.create_task(self._auto_scale_loop())
            
            # Begin main operation loop
            asyncio.create_task(self._operation_loop())
            
            self.status = AgentStatus.ACTIVE
            self._running = True
            
            self.logger.info(f"Agent {self.config.name} started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start agent: {e}")
            self.status = AgentStatus.ERROR
            return False
    
    async def stop(self) -> bool:
        """Stop the agent gracefully
        
        Returns:
            bool: True if successfully stopped, False otherwise
        """
        try:
            self.logger.info(f"Stopping {self.config.name} agent...")
            self._running = False
            
            # Stop autonomous knowledge learning
            if self._knowledge_learning_enabled:
                await self.knowledge_adapter.stop_autonomous_learning()
            
            # Perform cleanup
            await self._cleanup()
            
            self.status = AgentStatus.STOPPED
            self.logger.info(f"Agent {self.config.name} stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping agent: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check
        
        Returns:
            Dict containing health status and metrics
        """
        try:
            health_data = {
                "agent_id": self.agent_id,
                "name": self.config.name,
                "status": self.status.value,
                "uptime": (datetime.utcnow() - self.created_at).total_seconds(),
                "last_check": datetime.utcnow().isoformat(),
                "metrics": self.metrics.__dict__,
                "healthy": True
            }
            
            # Perform agent-specific health checks
            agent_health = await self._agent_health_check()
            health_data.update(agent_health)
            
            self.last_health_check = datetime.utcnow()
            return health_data
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "agent_id": self.agent_id,
                "healthy": False,
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming request
        
        Args:
            request: Request data
            
        Returns:
            Response data
        """
        try:
            # Log request for monitoring
            self.logger.debug(f"Processing request: {request.get('type', 'unknown')}")
            
            # Update metrics
            self.metrics.throughput_per_hour += 1
            
            # Process the request
            start_time = datetime.utcnow()
            response = await self._process_request(request)
            end_time = datetime.utcnow()
            
            # Update response time metrics
            response_time = (end_time - start_time).total_seconds() * 1000
            self.metrics.response_time_ms = (
                self.metrics.response_time_ms * 0.9 + response_time * 0.1
            )
            
            # Track revenue if applicable
            if self._revenue_tracking_enabled:
                await self._track_revenue(request, response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing request: {e}")
            self.metrics.error_rate += 0.1
            return {
                "error": str(e),
                "status": "failed",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # Abstract methods that must be implemented by agent subclasses
    
    @abstractmethod
    async def _initialize(self) -> None:
        """Initialize agent-specific components"""
        pass
    
    @abstractmethod
    async def _process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process agent-specific request logic"""
        pass
    
    @abstractmethod
    async def _agent_health_check(self) -> Dict[str, Any]:
        """Perform agent-specific health checks"""
        pass
    
    # Optional override methods
    
    async def _cleanup(self) -> None:
        """Cleanup agent resources (optional override)"""
        pass
    
    async def _track_revenue(self, request: Dict[str, Any], response: Dict[str, Any]) -> None:
        """Track revenue from request processing (optional override)"""
        # Default implementation - track basic usage
        revenue_amount = self._calculate_revenue(request, response)
        self.metrics.revenue_generated += revenue_amount
    
    def _calculate_revenue(self, request: Dict[str, Any], response: Dict[str, Any]) -> float:
        """Calculate revenue for a request (optional override)"""
        # Default: $0.01 per request
        return 0.01
    
    # Internal monitoring loops
    
    async def _health_check_loop(self) -> None:
        """Continuous health monitoring"""
        while self._running:
            try:
                await self.health_check()
                await asyncio.sleep(self._health_check_interval)
            except Exception as e:
                self.logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(self._health_check_interval)
    
    async def _revenue_tracking_loop(self) -> None:
        """Continuous revenue tracking and optimization"""
        while self._running:
            try:
                # Update revenue metrics
                await self._update_revenue_metrics()
                await asyncio.sleep(300)  # Every 5 minutes
            except Exception as e:
                self.logger.error(f"Revenue tracking error: {e}")
                await asyncio.sleep(300)
    
    async def _auto_scale_loop(self) -> None:
        """Continuous auto-scaling monitoring"""
        while self._running:
            try:
                # Check if scaling is needed
                await self._check_scaling_needs()
                await asyncio.sleep(60)  # Every minute
            except Exception as e:
                self.logger.error(f"Auto-scaling error: {e}")
                await asyncio.sleep(60)
    
    async def _operation_loop(self) -> None:
        """Main agent operation loop"""
        while self._running:
            try:
                # Perform periodic maintenance tasks
                await self._periodic_maintenance()
                await asyncio.sleep(3600)  # Every hour
            except Exception as e:
                self.logger.error(f"Operation loop error: {e}")
                await asyncio.sleep(3600)
    
    async def _update_revenue_metrics(self) -> None:
        """Update revenue-related metrics"""
        # Calculate uptime percentage
        uptime = (datetime.utcnow() - self.created_at).total_seconds()
        # Assuming 99.9% target uptime
        self.metrics.uptime_percentage = min(99.9, (uptime / (uptime + 10)) * 100)
    
    async def _check_scaling_needs(self) -> None:
        """Check if agent needs to scale up or down"""
        # Simple scaling logic based on response time and throughput
        if self.metrics.response_time_ms > 500:  # Scale up if response time > 500ms
            await self._scale_up()
        elif self.metrics.response_time_ms < 100 and self.metrics.throughput_per_hour < 10:
            await self._scale_down()
    
    async def _scale_up(self) -> None:
        """Scale up agent resources"""
        self.logger.info("Scaling up agent resources")
        self.status = AgentStatus.SCALING
        # Implementation would trigger infrastructure scaling
        self.status = AgentStatus.ACTIVE
    
    async def _scale_down(self) -> None:
        """Scale down agent resources"""
        self.logger.info("Scaling down agent resources")
        self.status = AgentStatus.SCALING
        # Implementation would trigger infrastructure scaling
        self.status = AgentStatus.ACTIVE
    
    async def _periodic_maintenance(self) -> None:
        """Perform periodic maintenance tasks"""
        # Reset hourly metrics
        self.metrics.throughput_per_hour = 0
        
        # Log current status
        self.logger.info(f"Agent status: {self.status.value}, "
                        f"Revenue: ${self.metrics.revenue_generated:.2f}, "
                        f"Uptime: {self.metrics.uptime_percentage:.1f}%")
    
    # Knowledge Adapter Integration Methods
    
    async def query_knowledge(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Query the agent's knowledge base
        
        Args:
            query: Search query for knowledge items
            limit: Maximum number of results to return
            
        Returns:
            List of knowledge items matching the query
        """
        try:
            knowledge_items = self.knowledge_adapter.query_knowledge(query, limit)
            return [
                {
                    "id": item.id,
                    "title": item.title,
                    "content": item.content[:500],  # Truncate for response
                    "source": item.metadata.get("source_url", "unknown"),
                    "relevance_score": item.relevance_score,
                    "content_type": item.content_type
                }
                for item in knowledge_items
            ]
        except Exception as e:
            self.logger.error(f"Error querying knowledge: {e}")
            return []
    
    async def get_profit_recommendations(self) -> List[Dict[str, Any]]:
        """Get profit optimization recommendations from knowledge adapter"""
        try:
            recommendations = await self.knowledge_adapter.get_profit_recommendations()
            self.logger.info(f"Generated {len(recommendations)} profit recommendations")
            return recommendations
        except Exception as e:
            self.logger.error(f"Error getting profit recommendations: {e}")
            return []
    
    async def enhance_capabilities_with_knowledge(self) -> List[str]:
        """Enhance agent capabilities using learned knowledge"""
        try:
            current_capabilities = getattr(self, '_capabilities', [])
            enhanced_capabilities = await self.knowledge_adapter.enhance_agent_capabilities(current_capabilities)
            
            # Update agent capabilities
            new_capabilities = [cap for cap in enhanced_capabilities if cap not in current_capabilities]
            if new_capabilities:
                self.logger.info(f"Enhanced capabilities with: {new_capabilities}")
                self._capabilities = enhanced_capabilities
            
            return enhanced_capabilities
        except Exception as e:
            self.logger.error(f"Error enhancing capabilities: {e}")
            return getattr(self, '_capabilities', [])
    
    def get_knowledge_summary(self) -> Dict[str, Any]:
        """Get summary of agent's knowledge state"""
        try:
            return self.knowledge_adapter.get_knowledge_summary()
        except Exception as e:
            self.logger.error(f"Error getting knowledge summary: {e}")
            return {"error": str(e)}
    
    async def add_custom_knowledge_source(self, name: str, url: str, 
                                        source_type: str = "github_repo",
                                        domain_tags: Optional[List[str]] = None) -> bool:
        """Add a custom knowledge source for the agent
        
        Args:
            name: Human-readable name for the source
            url: URL of the knowledge source
            source_type: Type of source (github_repo, documentation, etc.)
            domain_tags: Tags to categorize the knowledge
            
        Returns:
            True if source was added successfully
        """
        try:
            from .knowledge_adapter import KnowledgeSource, KnowledgeSourceType
            
            source = KnowledgeSource(
                id=f"custom_{name.lower().replace(' ', '_')}",
                name=name,
                url=url,
                source_type=KnowledgeSourceType(source_type),
                domain_tags=set(domain_tags or []),
                priority=5  # Medium priority for custom sources
            )
            
            success = self.knowledge_adapter.add_knowledge_source(source)
            if success:
                self.logger.info(f"Added custom knowledge source: {name}")
            return success
            
        except Exception as e:
            self.logger.error(f"Error adding custom knowledge source: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary representation"""
        base_dict = {
            "agent_id": self.agent_id,
            "config": self.config.__dict__,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "metrics": self.metrics.__dict__
        }
        
        # Add knowledge adapter summary
        try:
            base_dict["knowledge_summary"] = self.get_knowledge_summary()
        except Exception as e:
            base_dict["knowledge_summary"] = {"error": f"Failed to get knowledge summary: {e}"}
            
        return base_dict