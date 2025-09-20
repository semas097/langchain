"""Auto-Scaling Manager for AI Mega Agents Atlas

This module provides intelligent auto-scaling capabilities for agents
based on demand, performance metrics, and cost optimization.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json


class ScalingDirection(Enum):
    """Scaling direction types"""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


class ScalingTrigger(Enum):
    """Scaling trigger types"""
    CPU_THRESHOLD = "cpu_threshold"
    MEMORY_THRESHOLD = "memory_threshold"
    RESPONSE_TIME = "response_time"
    QUEUE_LENGTH = "queue_length"
    ERROR_RATE = "error_rate"
    REVENUE_OPTIMIZATION = "revenue_optimization"
    SCHEDULED = "scheduled"
    MANUAL = "manual"


@dataclass
class ScalingRule:
    """Auto-scaling rule definition"""
    rule_id: str
    name: str
    agent_type: str
    trigger: ScalingTrigger
    metric_threshold: float
    scaling_direction: ScalingDirection
    scaling_factor: float
    cooldown_seconds: int = 300
    max_instances: int = 10
    min_instances: int = 1
    conditions: Dict[str, Any] = field(default_factory=dict)
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ScalingEvent:
    """Scaling event record"""
    event_id: str
    agent_type: str
    instance_id: Optional[str]
    trigger: ScalingTrigger
    direction: ScalingDirection
    from_instances: int
    to_instances: int
    reason: str
    success: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metrics_snapshot: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceMetrics:
    """Resource utilization metrics"""
    cpu_percentage: float = 0.0
    memory_percentage: float = 0.0
    network_io_mbps: float = 0.0
    disk_io_mbps: float = 0.0
    response_time_ms: float = 0.0
    throughput_per_second: float = 0.0
    error_rate_percentage: float = 0.0
    queue_length: int = 0
    active_connections: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ScalingManager:
    """Intelligent auto-scaling manager for AI agents
    
    Provides capabilities for:
    - Real-time performance monitoring
    - Predictive scaling based on demand patterns
    - Cost-optimized resource allocation
    - Revenue-driven scaling decisions
    - Multi-dimensional scaling triggers
    - Automated instance management
    """
    
    def __init__(self):
        """Initialize the scaling manager"""
        self.logger = logging.getLogger("mega_agents.scaling")
        
        # Storage
        self._scaling_rules: Dict[str, ScalingRule] = {}
        self._scaling_events: List[ScalingEvent] = []
        self._resource_metrics: Dict[str, List[ResourceMetrics]] = {}
        self._instance_counts: Dict[str, int] = {}
        self._cooldown_timers: Dict[str, datetime] = {}
        
        # Configuration
        self._monitoring_interval = 30  # seconds
        self._metrics_retention_hours = 24
        self._predictive_scaling_enabled = True
        self._cost_optimization_enabled = True
        self._max_scaling_rate = 0.5  # Max 50% change per scaling event
        
        # Statistics
        self._total_scaling_events = 0
        self._successful_scaling_events = 0
        self._cost_savings = 0.0
        
        # Background tasks
        self._running = True
        self._tasks_started = False
    
    def _start_background_tasks(self):
        """Start background tasks if not already started"""
        if not self._tasks_started:
            try:
                asyncio.create_task(self._monitoring_loop())
                asyncio.create_task(self._scaling_decision_loop())
                asyncio.create_task(self._metrics_cleanup_loop())
                asyncio.create_task(self._predictive_scaling_loop())
                self._tasks_started = True
            except RuntimeError:
                # No event loop running, tasks will be started later
                pass

    def add_scaling_rule(
        self,
        name: str,
        agent_type: str,
        trigger: ScalingTrigger,
        metric_threshold: float,
        scaling_direction: ScalingDirection,
        scaling_factor: float = 1.5,
        cooldown_seconds: int = 300,
        max_instances: int = 10,
        min_instances: int = 1,
        conditions: Dict[str, Any] = None
    ) -> str:
        """Add a new auto-scaling rule
        
        Args:
            name: Rule name
            agent_type: Target agent type
            trigger: Scaling trigger type
            metric_threshold: Threshold value for trigger
            scaling_direction: UP or DOWN
            scaling_factor: Scaling multiplier
            cooldown_seconds: Cooldown period between scaling events
            max_instances: Maximum number of instances
            min_instances: Minimum number of instances
            conditions: Additional conditions for rule activation
            
        Returns:
            str: Rule ID
        """
        import uuid
        rule_id = str(uuid.uuid4())
        
        rule = ScalingRule(
            rule_id=rule_id,
            name=name,
            agent_type=agent_type,
            trigger=trigger,
            metric_threshold=metric_threshold,
            scaling_direction=scaling_direction,
            scaling_factor=scaling_factor,
            cooldown_seconds=cooldown_seconds,
            max_instances=max_instances,
            min_instances=min_instances,
            conditions=conditions or {}
        )
        
        self._scaling_rules[rule_id] = rule
        self.logger.info(f"Added scaling rule: {name} for {agent_type}")
        
        # Start background tasks if not started
        self._start_background_tasks()
        
        return rule_id
    
    async def update_metrics(
        self,
        agent_type: str,
        instance_id: str,
        metrics: ResourceMetrics
    ) -> None:
        """Update resource metrics for an agent instance
        
        Args:
            agent_type: Agent type
            instance_id: Instance identifier
            metrics: Resource metrics
        """
        key = f"{agent_type}:{instance_id}"
        
        if key not in self._resource_metrics:
            self._resource_metrics[key] = []
        
        self._resource_metrics[key].append(metrics)
        
        # Keep only recent metrics
        cutoff_time = datetime.utcnow() - timedelta(hours=self._metrics_retention_hours)
        self._resource_metrics[key] = [
            m for m in self._resource_metrics[key]
            if m.timestamp > cutoff_time
        ]
    
    async def trigger_scaling(
        self,
        agent_type: str,
        direction: ScalingDirection,
        reason: str = "Manual trigger",
        force: bool = False
    ) -> bool:
        """Manually trigger scaling for an agent type
        
        Args:
            agent_type: Agent type to scale
            direction: Scaling direction
            reason: Reason for scaling
            force: Force scaling even if in cooldown
            
        Returns:
            bool: True if scaling was triggered
        """
        try:
            current_instances = self._instance_counts.get(agent_type, 1)
            
            # Check cooldown unless forced
            if not force and self._is_in_cooldown(agent_type):
                self.logger.warning(f"Scaling blocked by cooldown for {agent_type}")
                return False
            
            # Calculate new instance count
            if direction == ScalingDirection.UP:
                new_instances = min(
                    int(current_instances * 1.5),
                    self._get_max_instances(agent_type)
                )
            else:
                new_instances = max(
                    int(current_instances * 0.7),
                    self._get_min_instances(agent_type)
                )
            
            if new_instances == current_instances:
                self.logger.info(f"No scaling needed for {agent_type}")
                return False
            
            # Execute scaling
            success = await self._execute_scaling(
                agent_type, current_instances, new_instances, 
                ScalingTrigger.MANUAL, reason
            )
            
            if success:
                self._instance_counts[agent_type] = new_instances
                self._cooldown_timers[agent_type] = datetime.utcnow()
            
            return success
            
        except Exception as e:
            self.logger.error(f"Manual scaling error for {agent_type}: {e}")
            return False
    
    async def get_scaling_recommendations(
        self,
        agent_type: str
    ) -> List[Dict[str, Any]]:
        """Get scaling recommendations for an agent type
        
        Args:
            agent_type: Agent type
            
        Returns:
            List of scaling recommendations
        """
        recommendations = []
        
        try:
            # Get current metrics
            current_metrics = self._get_aggregated_metrics(agent_type)
            if not current_metrics:
                return recommendations
            
            # Check each scaling rule
            for rule in self._scaling_rules.values():
                if rule.agent_type != agent_type or not rule.active:
                    continue
                
                recommendation = self._evaluate_scaling_rule(rule, current_metrics)
                if recommendation:
                    recommendations.append(recommendation)
            
            # Add predictive recommendations
            if self._predictive_scaling_enabled:
                predictive_rec = await self._get_predictive_recommendation(agent_type)
                if predictive_rec:
                    recommendations.append(predictive_rec)
            
            # Sort by priority
            recommendations.sort(key=lambda x: x.get("priority", 0), reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations for {agent_type}: {e}")
        
        return recommendations
    
    def _evaluate_scaling_rule(
        self,
        rule: ScalingRule,
        metrics: Dict[str, float]
    ) -> Optional[Dict[str, Any]]:
        """Evaluate a scaling rule against current metrics
        
        Args:
            rule: Scaling rule
            metrics: Current metrics
            
        Returns:
            Scaling recommendation if rule is triggered
        """
        try:
            # Get metric value based on trigger type
            metric_value = self._get_metric_value(rule.trigger, metrics)
            if metric_value is None:
                return None
            
            # Check if threshold is crossed
            threshold_crossed = False
            if rule.scaling_direction == ScalingDirection.UP:
                threshold_crossed = metric_value > rule.metric_threshold
            else:
                threshold_crossed = metric_value < rule.metric_threshold
            
            if not threshold_crossed:
                return None
            
            # Check additional conditions
            if not self._check_rule_conditions(rule, metrics):
                return None
            
            # Calculate priority based on how far over/under threshold
            threshold_deviation = abs(metric_value - rule.metric_threshold) / rule.metric_threshold
            priority = min(100, threshold_deviation * 100)
            
            return {
                "rule_id": rule.rule_id,
                "rule_name": rule.name,
                "trigger": rule.trigger.value,
                "direction": rule.scaling_direction.value,
                "metric_value": metric_value,
                "threshold": rule.metric_threshold,
                "scaling_factor": rule.scaling_factor,
                "priority": priority,
                "reason": f"{rule.trigger.value} {metric_value:.2f} crossed threshold {rule.metric_threshold:.2f}"
            }
            
        except Exception as e:
            self.logger.error(f"Error evaluating scaling rule {rule.rule_id}: {e}")
            return None
    
    def _get_metric_value(self, trigger: ScalingTrigger, metrics: Dict[str, float]) -> Optional[float]:
        """Get metric value for a trigger type
        
        Args:
            trigger: Scaling trigger
            metrics: Metrics dictionary
            
        Returns:
            Metric value if available
        """
        mapping = {
            ScalingTrigger.CPU_THRESHOLD: "cpu_percentage",
            ScalingTrigger.MEMORY_THRESHOLD: "memory_percentage",
            ScalingTrigger.RESPONSE_TIME: "response_time_ms",
            ScalingTrigger.QUEUE_LENGTH: "queue_length",
            ScalingTrigger.ERROR_RATE: "error_rate_percentage"
        }
        
        metric_key = mapping.get(trigger)
        return metrics.get(metric_key) if metric_key else None
    
    def _check_rule_conditions(self, rule: ScalingRule, metrics: Dict[str, float]) -> bool:
        """Check if rule conditions are met
        
        Args:
            rule: Scaling rule
            metrics: Current metrics
            
        Returns:
            bool: True if conditions are met
        """
        for condition, expected_value in rule.conditions.items():
            actual_value = metrics.get(condition)
            if actual_value is None or actual_value != expected_value:
                return False
        return True
    
    def _get_aggregated_metrics(self, agent_type: str) -> Dict[str, float]:
        """Get aggregated metrics for an agent type
        
        Args:
            agent_type: Agent type
            
        Returns:
            Aggregated metrics
        """
        all_metrics = []
        
        # Collect metrics from all instances of the agent type
        for key, metrics_list in self._resource_metrics.items():
            if key.startswith(f"{agent_type}:"):
                # Get recent metrics (last 5 minutes)
                recent_cutoff = datetime.utcnow() - timedelta(minutes=5)
                recent_metrics = [m for m in metrics_list if m.timestamp > recent_cutoff]
                all_metrics.extend(recent_metrics)
        
        if not all_metrics:
            return {}
        
        # Calculate averages
        return {
            "cpu_percentage": sum(m.cpu_percentage for m in all_metrics) / len(all_metrics),
            "memory_percentage": sum(m.memory_percentage for m in all_metrics) / len(all_metrics),
            "response_time_ms": sum(m.response_time_ms for m in all_metrics) / len(all_metrics),
            "throughput_per_second": sum(m.throughput_per_second for m in all_metrics) / len(all_metrics),
            "error_rate_percentage": sum(m.error_rate_percentage for m in all_metrics) / len(all_metrics),
            "queue_length": sum(m.queue_length for m in all_metrics) / len(all_metrics),
            "active_connections": sum(m.active_connections for m in all_metrics) / len(all_metrics)
        }
    
    async def _get_predictive_recommendation(self, agent_type: str) -> Optional[Dict[str, Any]]:
        """Get predictive scaling recommendation based on historical patterns
        
        Args:
            agent_type: Agent type
            
        Returns:
            Predictive recommendation if applicable
        """
        try:
            # Analyze historical patterns
            historical_metrics = self._get_historical_metrics(agent_type, hours=24)
            if len(historical_metrics) < 10:  # Need enough data
                return None
            
            # Simple trend analysis
            recent_metrics = historical_metrics[-5:]
            older_metrics = historical_metrics[-10:-5]
            
            recent_avg_cpu = sum(m.cpu_percentage for m in recent_metrics) / len(recent_metrics)
            older_avg_cpu = sum(m.cpu_percentage for m in older_metrics) / len(older_metrics)
            
            trend = (recent_avg_cpu - older_avg_cpu) / older_avg_cpu if older_avg_cpu > 0 else 0
            
            # Predict if trend continues
            if trend > 0.1:  # 10% increase trend
                return {
                    "type": "predictive",
                    "direction": ScalingDirection.UP.value,
                    "reason": f"Upward trend detected: {trend:.1%} CPU increase",
                    "priority": 30,
                    "confidence": min(100, abs(trend) * 100)
                }
            elif trend < -0.1:  # 10% decrease trend
                return {
                    "type": "predictive",
                    "direction": ScalingDirection.DOWN.value,
                    "reason": f"Downward trend detected: {trend:.1%} CPU decrease",
                    "priority": 20,
                    "confidence": min(100, abs(trend) * 100)
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Predictive analysis error for {agent_type}: {e}")
            return None
    
    def _get_historical_metrics(self, agent_type: str, hours: int = 24) -> List[ResourceMetrics]:
        """Get historical metrics for an agent type
        
        Args:
            agent_type: Agent type
            hours: Hours of history to retrieve
            
        Returns:
            List of historical metrics
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        historical_metrics = []
        
        for key, metrics_list in self._resource_metrics.items():
            if key.startswith(f"{agent_type}:"):
                historical_metrics.extend([
                    m for m in metrics_list if m.timestamp > cutoff_time
                ])
        
        # Sort by timestamp
        historical_metrics.sort(key=lambda m: m.timestamp)
        return historical_metrics
    
    async def _execute_scaling(
        self,
        agent_type: str,
        from_instances: int,
        to_instances: int,
        trigger: ScalingTrigger,
        reason: str
    ) -> bool:
        """Execute the actual scaling operation
        
        Args:
            agent_type: Agent type
            from_instances: Current instance count
            to_instances: Target instance count
            trigger: Scaling trigger
            reason: Scaling reason
            
        Returns:
            bool: True if successful
        """
        try:
            import uuid
            event_id = str(uuid.uuid4())
            
            direction = (
                ScalingDirection.UP if to_instances > from_instances
                else ScalingDirection.DOWN
            )
            
            self.logger.info(
                f"Executing scaling for {agent_type}: {from_instances} -> {to_instances} "
                f"(trigger: {trigger.value})"
            )
            
            # In a real implementation, this would interface with container orchestration
            # For now, we'll simulate the scaling operation
            success = await self._simulate_scaling_operation(agent_type, to_instances)
            
            # Record scaling event
            event = ScalingEvent(
                event_id=event_id,
                agent_type=agent_type,
                instance_id=None,
                trigger=trigger,
                direction=direction,
                from_instances=from_instances,
                to_instances=to_instances,
                reason=reason,
                success=success,
                metrics_snapshot=self._get_aggregated_metrics(agent_type)
            )
            
            self._scaling_events.append(event)
            self._total_scaling_events += 1
            
            if success:
                self._successful_scaling_events += 1
                
                # Calculate cost impact
                cost_impact = self._calculate_cost_impact(from_instances, to_instances)
                if cost_impact < 0:  # Cost savings
                    self._cost_savings += abs(cost_impact)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Scaling execution error: {e}")
            return False
    
    async def _simulate_scaling_operation(self, agent_type: str, target_instances: int) -> bool:
        """Simulate scaling operation (replace with real implementation)
        
        Args:
            agent_type: Agent type
            target_instances: Target instance count
            
        Returns:
            bool: True if successful
        """
        # Simulate operation delay
        await asyncio.sleep(1)
        
        # In real implementation, this would:
        # 1. Update Kubernetes deployments
        # 2. Wait for pods to be ready
        # 3. Update load balancer configuration
        # 4. Verify health checks
        
        # For simulation, assume 95% success rate
        import random
        return random.random() < 0.95
    
    def _calculate_cost_impact(self, from_instances: int, to_instances: int) -> float:
        """Calculate cost impact of scaling operation
        
        Args:
            from_instances: Current instances
            to_instances: Target instances
            
        Returns:
            float: Cost change (positive = increase, negative = savings)
        """
        # Assume $0.10 per instance per hour
        hourly_cost_per_instance = 0.10
        instance_diff = to_instances - from_instances
        return instance_diff * hourly_cost_per_instance
    
    def _is_in_cooldown(self, agent_type: str) -> bool:
        """Check if agent type is in cooldown period
        
        Args:
            agent_type: Agent type
            
        Returns:
            bool: True if in cooldown
        """
        if agent_type not in self._cooldown_timers:
            return False
        
        last_scaling = self._cooldown_timers[agent_type]
        cooldown_duration = timedelta(seconds=300)  # Default 5 minutes
        
        return datetime.utcnow() - last_scaling < cooldown_duration
    
    def _get_max_instances(self, agent_type: str) -> int:
        """Get maximum instances for agent type
        
        Args:
            agent_type: Agent type
            
        Returns:
            int: Maximum instances
        """
        for rule in self._scaling_rules.values():
            if rule.agent_type == agent_type:
                return rule.max_instances
        return 10  # Default maximum
    
    def _get_min_instances(self, agent_type: str) -> int:
        """Get minimum instances for agent type
        
        Args:
            agent_type: Agent type
            
        Returns:
            int: Minimum instances
        """
        for rule in self._scaling_rules.values():
            if rule.agent_type == agent_type:
                return rule.min_instances
        return 1  # Default minimum
    
    async def get_scaling_status(self) -> Dict[str, Any]:
        """Get comprehensive scaling status
        
        Returns:
            Scaling status and statistics
        """
        # Recent scaling events (last 24 hours)
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_events = [
            e for e in self._scaling_events
            if e.timestamp > recent_cutoff
        ]
        
        return {
            "total_scaling_rules": len(self._scaling_rules),
            "active_scaling_rules": len([r for r in self._scaling_rules.values() if r.active]),
            "total_scaling_events": self._total_scaling_events,
            "successful_scaling_events": self._successful_scaling_events,
            "success_rate": (
                self._successful_scaling_events / self._total_scaling_events * 100
                if self._total_scaling_events > 0 else 0
            ),
            "recent_events_24h": len(recent_events),
            "cost_savings": self._cost_savings,
            "monitored_agent_types": len(set(
                key.split(":")[0] for key in self._resource_metrics.keys()
            )),
            "instance_counts": self._instance_counts.copy(),
            "predictive_scaling_enabled": self._predictive_scaling_enabled,
            "cost_optimization_enabled": self._cost_optimization_enabled,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    async def _monitoring_loop(self) -> None:
        """Background monitoring loop"""
        while self._running:
            try:
                # Monitor resource usage and trigger alerts if needed
                for agent_type in set(key.split(":")[0] for key in self._resource_metrics.keys()):
                    metrics = self._get_aggregated_metrics(agent_type)
                    
                    # Check for critical thresholds
                    if metrics.get("cpu_percentage", 0) > 90:
                        self.logger.warning(f"High CPU usage for {agent_type}: {metrics['cpu_percentage']:.1f}%")
                    
                    if metrics.get("error_rate_percentage", 0) > 5:
                        self.logger.warning(f"High error rate for {agent_type}: {metrics['error_rate_percentage']:.1f}%")
                
                await asyncio.sleep(self._monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(self._monitoring_interval)
    
    async def _scaling_decision_loop(self) -> None:
        """Background scaling decision loop"""
        while self._running:
            try:
                # Check all agent types for scaling opportunities
                agent_types = set(key.split(":")[0] for key in self._resource_metrics.keys())
                
                for agent_type in agent_types:
                    if self._is_in_cooldown(agent_type):
                        continue
                    
                    recommendations = await self.get_scaling_recommendations(agent_type)
                    
                    # Execute highest priority recommendation
                    if recommendations:
                        top_rec = recommendations[0]
                        if top_rec.get("priority", 0) > 80:  # High priority threshold
                            direction = ScalingDirection(top_rec["direction"])
                            await self.trigger_scaling(
                                agent_type, direction, top_rec["reason"]
                            )
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Scaling decision loop error: {e}")
                await asyncio.sleep(60)
    
    async def _metrics_cleanup_loop(self) -> None:
        """Background metrics cleanup loop"""
        while self._running:
            try:
                cutoff_time = datetime.utcnow() - timedelta(hours=self._metrics_retention_hours)
                
                # Clean old metrics
                for key in list(self._resource_metrics.keys()):
                    self._resource_metrics[key] = [
                        m for m in self._resource_metrics[key]
                        if m.timestamp > cutoff_time
                    ]
                    
                    # Remove empty entries
                    if not self._resource_metrics[key]:
                        del self._resource_metrics[key]
                
                # Clean old scaling events
                old_events_cutoff = datetime.utcnow() - timedelta(days=30)
                self._scaling_events = [
                    e for e in self._scaling_events
                    if e.timestamp > old_events_cutoff
                ]
                
                await asyncio.sleep(3600)  # Clean every hour
                
            except Exception as e:
                self.logger.error(f"Metrics cleanup error: {e}")
                await asyncio.sleep(3600)
    
    async def _predictive_scaling_loop(self) -> None:
        """Background predictive scaling loop"""
        while self._running:
            try:
                if not self._predictive_scaling_enabled:
                    await asyncio.sleep(1800)  # Check every 30 minutes
                    continue
                
                # Perform predictive analysis for all agent types
                agent_types = set(key.split(":")[0] for key in self._resource_metrics.keys())
                
                for agent_type in agent_types:
                    recommendation = await self._get_predictive_recommendation(agent_type)
                    
                    if (recommendation and 
                        recommendation.get("confidence", 0) > 70 and
                        not self._is_in_cooldown(agent_type)):
                        
                        direction = ScalingDirection(recommendation["direction"])
                        await self.trigger_scaling(
                            agent_type, direction, 
                            f"Predictive: {recommendation['reason']}"
                        )
                
                await asyncio.sleep(1800)  # Every 30 minutes
                
            except Exception as e:
                self.logger.error(f"Predictive scaling loop error: {e}")
                await asyncio.sleep(1800)
    
    async def shutdown(self) -> None:
        """Shutdown scaling manager"""
        self.logger.info("Shutting down scaling manager...")
        self._running = False


# Global scaling manager instance
scaling_manager = ScalingManager()