"""Agent Registry for AI Mega Agents Atlas

This module provides centralized agent discovery, management, and orchestration
capabilities for the enterprise agent ecosystem.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Type
from datetime import datetime
from dataclasses import dataclass
import json

from .base_agent import BaseAgent, AgentConfig, AgentStatus


@dataclass
class AgentRegistration:
    """Agent registration information"""
    agent_class: Type[BaseAgent]
    agent_type: str
    name: str
    description: str
    version: str
    capabilities: List[str]
    revenue_models: List[str]
    resource_requirements: Dict[str, Any]
    dependencies: List[str]
    registration_time: datetime


class AgentRegistry:
    """Central registry for managing all AI agents
    
    Provides capabilities for:
    - Agent discovery and registration
    - Instance management and orchestration
    - Health monitoring and status tracking
    - Load balancing and scaling coordination
    - Revenue tracking across agents
    """
    
    def __init__(self):
        """Initialize the agent registry"""
        self.logger = logging.getLogger("mega_agents.registry")
        
        # Registry storage
        self._registered_agents: Dict[str, AgentRegistration] = {}
        self._agent_instances: Dict[str, BaseAgent] = {}
        self._agent_health: Dict[str, Dict[str, Any]] = {}
        
        # Statistics
        self._total_requests_processed = 0
        self._total_revenue_generated = 0.0
        self._registry_start_time = datetime.utcnow()
        
        # Configuration
        self._health_check_interval = 60  # seconds
        self._auto_deploy_enabled = True
        self._load_balancing_enabled = True
        
        # Start monitoring tasks
        self._running = True
        self._tasks_started = False
    
    def _start_background_tasks(self):
        """Start background tasks if not already started"""
        if not self._tasks_started:
            try:
                asyncio.create_task(self._health_monitoring_loop())
                asyncio.create_task(self._statistics_loop())
                self._tasks_started = True
            except RuntimeError:
                # No event loop running, tasks will be started later
                pass

    def register_agent_type(
        self,
        agent_class: Type[BaseAgent],
        agent_type: str,
        name: str,
        description: str = "",
        version: str = "1.0.0",
        capabilities: List[str] = None,
        revenue_models: List[str] = None,
        resource_requirements: Dict[str, Any] = None,
        dependencies: List[str] = None
    ) -> bool:
        """Register a new agent type in the registry
        
        Args:
            agent_class: Agent class to register
            agent_type: Unique agent type identifier
            name: Human-readable agent name
            description: Agent description
            version: Agent version
            capabilities: List of agent capabilities
            revenue_models: Supported revenue models
            resource_requirements: Resource requirements
            dependencies: Agent dependencies
            
        Returns:
            bool: True if successfully registered
        """
        try:
            registration = AgentRegistration(
                agent_class=agent_class,
                agent_type=agent_type,
                name=name,
                description=description,
                version=version,
                capabilities=capabilities or [],
                revenue_models=revenue_models or [],
                resource_requirements=resource_requirements or {},
                dependencies=dependencies or [],
                registration_time=datetime.utcnow()
            )
            
            self._registered_agents[agent_type] = registration
            self.logger.info(f"Registered agent type: {agent_type} ({name})")
            
            # Start background tasks if not started
            self._start_background_tasks()
            
            # Auto-deploy if enabled
            if self._auto_deploy_enabled:
                try:
                    asyncio.create_task(self._auto_deploy_agent(agent_type))
                except RuntimeError:
                    # No event loop, auto-deploy will happen later
                    pass
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register agent type {agent_type}: {e}")
            return False
    
    async def create_agent_instance(
        self,
        agent_type: str,
        instance_id: Optional[str] = None,
        custom_config: Dict[str, Any] = None
    ) -> Optional[str]:
        """Create a new agent instance
        
        Args:
            agent_type: Type of agent to create
            instance_id: Optional custom instance ID
            custom_config: Optional custom configuration
            
        Returns:
            str: Instance ID if successful, None otherwise
        """
        try:
            if agent_type not in self._registered_agents:
                self.logger.error(f"Agent type {agent_type} not registered")
                return None
            
            registration = self._registered_agents[agent_type]
            
            # Create agent configuration
            config = AgentConfig(
                name=registration.name,
                agent_type=agent_type,
                version=registration.version,
                description=registration.description,
                custom_config=custom_config or {}
            )
            
            # Create agent instance
            agent_instance = registration.agent_class(config)
            
            # Use provided instance ID or generate one
            if instance_id is None:
                instance_id = f"{agent_type}_{agent_instance.agent_id[:8]}"
            
            # Store instance
            self._agent_instances[instance_id] = agent_instance
            
            # Start the agent
            success = await agent_instance.start()
            if not success:
                del self._agent_instances[instance_id]
                return None
            
            self.logger.info(f"Created agent instance: {instance_id}")
            return instance_id
            
        except Exception as e:
            self.logger.error(f"Failed to create agent instance: {e}")
            return None
    
    async def get_agent_instance(self, instance_id: str) -> Optional[BaseAgent]:
        """Get agent instance by ID
        
        Args:
            instance_id: Agent instance ID
            
        Returns:
            BaseAgent instance if found, None otherwise
        """
        return self._agent_instances.get(instance_id)
    
    async def remove_agent_instance(self, instance_id: str) -> bool:
        """Remove agent instance
        
        Args:
            instance_id: Agent instance ID
            
        Returns:
            bool: True if successfully removed
        """
        try:
            if instance_id not in self._agent_instances:
                return False
            
            agent = self._agent_instances[instance_id]
            await agent.stop()
            del self._agent_instances[instance_id]
            
            if instance_id in self._agent_health:
                del self._agent_health[instance_id]
            
            self.logger.info(f"Removed agent instance: {instance_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove agent instance {instance_id}: {e}")
            return False
    
    async def route_request(
        self,
        agent_type: str,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route request to appropriate agent instance
        
        Args:
            agent_type: Target agent type
            request: Request data
            
        Returns:
            Response from agent
        """
        try:
            # Find available instances of the requested type
            available_instances = [
                instance_id for instance_id, agent in self._agent_instances.items()
                if agent.config.agent_type == agent_type and agent.status == AgentStatus.ACTIVE
            ]
            
            if not available_instances:
                # Auto-create instance if none available
                instance_id = await self.create_agent_instance(agent_type)
                if instance_id:
                    available_instances = [instance_id]
                else:
                    return {
                        "error": f"No available instances for agent type: {agent_type}",
                        "status": "failed"
                    }
            
            # Load balancing - choose least loaded instance
            selected_instance = self._select_best_instance(available_instances)
            agent = self._agent_instances[selected_instance]
            
            # Process request
            response = await agent.process_request(request)
            self._total_requests_processed += 1
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error routing request: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    def list_registered_agents(self) -> Dict[str, Dict[str, Any]]:
        """List all registered agent types
        
        Returns:
            Dictionary of registered agent information
        """
        return {
            agent_type: {
                "name": reg.name,
                "description": reg.description,
                "version": reg.version,
                "capabilities": reg.capabilities,
                "revenue_models": reg.revenue_models,
                "resource_requirements": reg.resource_requirements,
                "dependencies": reg.dependencies,
                "registration_time": reg.registration_time.isoformat()
            }
            for agent_type, reg in self._registered_agents.items()
        }
    
    def list_agent_instances(self) -> Dict[str, Dict[str, Any]]:
        """List all active agent instances
        
        Returns:
            Dictionary of active agent instances
        """
        return {
            instance_id: agent.to_dict()
            for instance_id, agent in self._agent_instances.items()
        }
    
    async def get_registry_status(self) -> Dict[str, Any]:
        """Get comprehensive registry status
        
        Returns:
            Registry status and statistics
        """
        uptime = (datetime.utcnow() - self._registry_start_time).total_seconds()
        
        # Calculate total revenue
        total_revenue = sum(
            agent.metrics.revenue_generated
            for agent in self._agent_instances.values()
        )
        
        # Count agents by status
        status_counts = {}
        for agent in self._agent_instances.values():
            status = agent.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "registry_uptime_seconds": uptime,
            "total_registered_types": len(self._registered_agents),
            "total_active_instances": len(self._agent_instances),
            "total_requests_processed": self._total_requests_processed,
            "total_revenue_generated": total_revenue,
            "agents_by_status": status_counts,
            "health_check_interval": self._health_check_interval,
            "auto_deploy_enabled": self._auto_deploy_enabled,
            "load_balancing_enabled": self._load_balancing_enabled,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def _select_best_instance(self, instance_ids: List[str]) -> str:
        """Select the best instance for load balancing
        
        Args:
            instance_ids: Available instance IDs
            
        Returns:
            Selected instance ID
        """
        if not self._load_balancing_enabled or len(instance_ids) == 1:
            return instance_ids[0]
        
        # Simple load balancing based on response time and throughput
        best_instance = instance_ids[0]
        best_score = float('inf')
        
        for instance_id in instance_ids:
            agent = self._agent_instances[instance_id]
            # Score based on response time and current load
            score = (
                agent.metrics.response_time_ms +
                agent.metrics.throughput_per_hour * 0.1
            )
            
            if score < best_score:
                best_score = score
                best_instance = instance_id
        
        return best_instance
    
    async def _auto_deploy_agent(self, agent_type: str) -> None:
        """Auto-deploy an agent instance
        
        Args:
            agent_type: Agent type to deploy
        """
        try:
            instance_id = await self.create_agent_instance(agent_type)
            if instance_id:
                self.logger.info(f"Auto-deployed agent: {instance_id}")
            else:
                self.logger.warning(f"Failed to auto-deploy agent type: {agent_type}")
        except Exception as e:
            self.logger.error(f"Auto-deploy error for {agent_type}: {e}")
    
    async def _health_monitoring_loop(self) -> None:
        """Continuous health monitoring for all instances"""
        while self._running:
            try:
                for instance_id, agent in self._agent_instances.items():
                    health_data = await agent.health_check()
                    self._agent_health[instance_id] = health_data
                    
                    # Handle unhealthy agents
                    if not health_data.get("healthy", False):
                        self.logger.warning(f"Unhealthy agent detected: {instance_id}")
                        # Could implement auto-recovery here
                
                await asyncio.sleep(self._health_check_interval)
                
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(self._health_check_interval)
    
    async def _statistics_loop(self) -> None:
        """Update registry statistics"""
        while self._running:
            try:
                # Update total revenue
                self._total_revenue_generated = sum(
                    agent.metrics.revenue_generated
                    for agent in self._agent_instances.items()
                )
                
                # Log statistics
                status = await self.get_registry_status()
                self.logger.info(
                    f"Registry Stats - Instances: {status['total_active_instances']}, "
                    f"Requests: {status['total_requests_processed']}, "
                    f"Revenue: ${status['total_revenue_generated']:.2f}"
                )
                
                await asyncio.sleep(300)  # Every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Statistics loop error: {e}")
                await asyncio.sleep(300)
    
    async def shutdown(self) -> None:
        """Shutdown the registry and all agents"""
        self.logger.info("Shutting down agent registry...")
        self._running = False
        
        # Stop all agent instances
        for instance_id in list(self._agent_instances.keys()):
            await self.remove_agent_instance(instance_id)
        
        self.logger.info("Agent registry shutdown complete")


# Global registry instance
agent_registry = AgentRegistry()