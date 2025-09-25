"""Subscription and monetization system for mega agents."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from langchain_community.agent_toolkits.ai_mega_agents_factory.base import (
    MonetizationTier,
)
from langchain_community.agent_toolkits.ai_mega_agents_factory.factory import (
    AgentType,
)


class SubscriptionStatus(str, Enum):
    """Subscription status values."""
    
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PaymentMethod(str, Enum):
    """Payment method types."""
    
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    CRYPTO = "crypto"
    ENTERPRISE_CONTRACT = "enterprise_contract"


class UsageMetric(BaseModel):
    """Usage metric for billing."""
    
    metric_name: str = Field(description="Name of the metric")
    value: float = Field(description="Metric value")
    unit: str = Field(description="Unit of measurement")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Subscription(BaseModel):
    """Subscription model."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(description="User ID")
    tier: MonetizationTier = Field(description="Subscription tier")
    status: SubscriptionStatus = Field(default=SubscriptionStatus.ACTIVE)
    
    # Dates
    created_at: datetime = Field(default_factory=datetime.utcnow)
    start_date: datetime = Field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = None
    last_payment_date: Optional[datetime] = None
    next_payment_date: Optional[datetime] = None
    
    # Billing
    monthly_fee: float = Field(default=0.0, description="Monthly subscription fee")
    usage_rate: float = Field(default=0.0, description="Per-usage rate")
    credit_balance: float = Field(default=0.0, description="Prepaid credits")
    
    # Limits
    monthly_request_limit: Optional[int] = None
    concurrent_agent_limit: Optional[int] = None
    api_rate_limit: Optional[int] = None
    
    # Features
    enabled_agents: List[AgentType] = Field(default_factory=list)
    premium_features: List[str] = Field(default_factory=list)


class BillingRecord(BaseModel):
    """Billing record for usage tracking."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subscription_id: str = Field(description="Associated subscription ID")
    user_id: str = Field(description="User ID")
    
    # Usage details
    agent_type: AgentType = Field(description="Agent type used")
    execution_count: int = Field(default=1, description="Number of executions")
    compute_time: float = Field(default=0.0, description="Compute time in seconds")
    input_tokens: int = Field(default=0, description="Input tokens processed")
    output_tokens: int = Field(default=0, description="Output tokens generated")
    
    # Billing
    unit_cost: float = Field(default=0.0, description="Cost per unit")
    total_cost: float = Field(default=0.0, description="Total cost")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    processed: bool = Field(default=False, description="Whether billing was processed")


class SubscriptionManager:
    """Manager for subscriptions and billing."""
    
    def __init__(self):
        """Initialize the subscription manager."""
        self._subscriptions: Dict[str, Subscription] = {}
        self._billing_records: List[BillingRecord] = []
        self._pricing_tiers = self._initialize_pricing_tiers()
    
    def _initialize_pricing_tiers(self) -> Dict[MonetizationTier, Dict[str, Any]]:
        """Initialize pricing tier configurations."""
        return {
            MonetizationTier.FREE: {
                "monthly_fee": 0.0,
                "usage_rate": 0.0,
                "monthly_request_limit": 100,
                "concurrent_agent_limit": 1,
                "api_rate_limit": 10,  # requests per minute
                "enabled_agents": [
                    AgentType.ETL_AGENT,
                    AgentType.DATA_VALIDATION_AGENT,
                    AgentType.EMAIL_AGENT,
                ],
                "premium_features": [],
            },
            MonetizationTier.BASIC: {
                "monthly_fee": 29.99,
                "usage_rate": 0.01,  # per execution
                "monthly_request_limit": 10000,
                "concurrent_agent_limit": 5,
                "api_rate_limit": 100,
                "enabled_agents": list(AgentType)[:20],  # First 20 agents
                "premium_features": ["analytics", "email_support"],
            },
            MonetizationTier.PROFESSIONAL: {
                "monthly_fee": 99.99,
                "usage_rate": 0.005,
                "monthly_request_limit": 100000,
                "concurrent_agent_limit": 20,
                "api_rate_limit": 1000,
                "enabled_agents": list(AgentType)[:38],  # All core agents
                "premium_features": [
                    "analytics",
                    "priority_support",
                    "custom_agents",
                    "webhooks",
                ],
            },
            MonetizationTier.ENTERPRISE: {
                "monthly_fee": 499.99,
                "usage_rate": 0.001,
                "monthly_request_limit": None,  # Unlimited
                "concurrent_agent_limit": None,  # Unlimited
                "api_rate_limit": None,  # Unlimited
                "enabled_agents": list(AgentType),  # All agents
                "premium_features": [
                    "analytics",
                    "dedicated_support",
                    "custom_agents",
                    "webhooks",
                    "on_premise_deployment",
                    "sla_guarantee",
                    "custom_integrations",
                ],
            },
        }
    
    def create_subscription(
        self,
        user_id: str,
        tier: MonetizationTier,
        payment_method: PaymentMethod = PaymentMethod.CREDIT_CARD,
    ) -> Subscription:
        """Create a new subscription.
        
        Args:
            user_id: User ID
            tier: Subscription tier
            payment_method: Payment method
            
        Returns:
            Created subscription
        """
        tier_config = self._pricing_tiers[tier]
        
        subscription = Subscription(
            user_id=user_id,
            tier=tier,
            monthly_fee=tier_config["monthly_fee"],
            usage_rate=tier_config["usage_rate"],
            monthly_request_limit=tier_config["monthly_request_limit"],
            concurrent_agent_limit=tier_config["concurrent_agent_limit"],
            api_rate_limit=tier_config["api_rate_limit"],
            enabled_agents=tier_config["enabled_agents"],
            premium_features=tier_config["premium_features"],
        )
        
        # Set next payment date
        if tier != MonetizationTier.FREE:
            subscription.next_payment_date = datetime.utcnow() + timedelta(days=30)
        
        self._subscriptions[subscription.id] = subscription
        return subscription
    
    def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Get subscription by ID.
        
        Args:
            subscription_id: Subscription ID
            
        Returns:
            Subscription or None if not found
        """
        return self._subscriptions.get(subscription_id)
    
    def get_user_subscription(self, user_id: str) -> Optional[Subscription]:
        """Get active subscription for user.
        
        Args:
            user_id: User ID
            
        Returns:
            Active subscription or None
        """
        for subscription in self._subscriptions.values():
            if (subscription.user_id == user_id and 
                subscription.status == SubscriptionStatus.ACTIVE):
                return subscription
        return None
    
    def validate_usage(
        self,
        user_id: str,
        agent_type: AgentType,
    ) -> Dict[str, Any]:
        """Validate if user can use the agent.
        
        Args:
            user_id: User ID
            agent_type: Agent type to validate
            
        Returns:
            Validation result with allowed status and details
        """
        subscription = self.get_user_subscription(user_id)
        
        if subscription is None:
            return {
                "allowed": False,
                "reason": "No active subscription",
                "upgrade_required": True,
            }
        
        # Check if agent is enabled for this tier
        if agent_type not in subscription.enabled_agents:
            return {
                "allowed": False,
                "reason": f"Agent {agent_type.value} not available in {subscription.tier.value} tier",
                "upgrade_required": True,
            }
        
        # Check request limits
        if subscription.monthly_request_limit is not None:
            current_usage = self._get_monthly_usage(user_id)
            if current_usage >= subscription.monthly_request_limit:
                return {
                    "allowed": False,
                    "reason": "Monthly request limit exceeded",
                    "current_usage": current_usage,
                    "limit": subscription.monthly_request_limit,
                }
        
        return {
            "allowed": True,
            "subscription_tier": subscription.tier.value,
            "usage_rate": subscription.usage_rate,
        }
    
    def record_usage(
        self,
        user_id: str,
        agent_type: AgentType,
        execution_count: int = 1,
        compute_time: float = 0.0,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> BillingRecord:
        """Record usage for billing.
        
        Args:
            user_id: User ID
            agent_type: Agent type used
            execution_count: Number of executions
            compute_time: Compute time in seconds
            input_tokens: Input tokens processed
            output_tokens: Output tokens generated
            
        Returns:
            Created billing record
        """
        subscription = self.get_user_subscription(user_id)
        if subscription is None:
            raise ValueError("No active subscription found")
        
        # Calculate cost
        unit_cost = subscription.usage_rate
        total_cost = unit_cost * execution_count
        
        # Add token-based pricing for AI/ML agents
        if "ai_ml" in agent_type.value or "nlp" in agent_type.value:
            token_cost = (input_tokens * 0.0001) + (output_tokens * 0.0002)
            total_cost += token_cost
        
        billing_record = BillingRecord(
            subscription_id=subscription.id,
            user_id=user_id,
            agent_type=agent_type,
            execution_count=execution_count,
            compute_time=compute_time,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            unit_cost=unit_cost,
            total_cost=total_cost,
        )
        
        self._billing_records.append(billing_record)
        return billing_record
    
    def _get_monthly_usage(self, user_id: str) -> int:
        """Get monthly usage count for user.
        
        Args:
            user_id: User ID
            
        Returns:
            Monthly usage count
        """
        current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        return sum(
            record.execution_count
            for record in self._billing_records
            if (record.user_id == user_id and 
                record.timestamp >= current_month)
        )
    
    def get_usage_report(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get usage report for user.
        
        Args:
            user_id: User ID
            start_date: Start date for report
            end_date: End date for report
            
        Returns:
            Usage report
        """
        if start_date is None:
            start_date = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if end_date is None:
            end_date = datetime.utcnow()
        
        user_records = [
            record for record in self._billing_records
            if (record.user_id == user_id and 
                start_date <= record.timestamp <= end_date)
        ]
        
        total_executions = sum(record.execution_count for record in user_records)
        total_cost = sum(record.total_cost for record in user_records)
        total_compute_time = sum(record.compute_time for record in user_records)
        
        agent_usage = {}
        for record in user_records:
            agent_type = record.agent_type.value
            if agent_type not in agent_usage:
                agent_usage[agent_type] = {
                    "executions": 0,
                    "cost": 0.0,
                    "compute_time": 0.0,
                }
            agent_usage[agent_type]["executions"] += record.execution_count
            agent_usage[agent_type]["cost"] += record.total_cost
            agent_usage[agent_type]["compute_time"] += record.compute_time
        
        return {
            "user_id": user_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "summary": {
                "total_executions": total_executions,
                "total_cost": total_cost,
                "total_compute_time": total_compute_time,
            },
            "agent_usage": agent_usage,
        }
    
    def upgrade_subscription(
        self,
        subscription_id: str,
        new_tier: MonetizationTier,
    ) -> Subscription:
        """Upgrade subscription to new tier.
        
        Args:
            subscription_id: Subscription ID
            new_tier: New tier to upgrade to
            
        Returns:
            Updated subscription
            
        Raises:
            ValueError: If subscription not found or invalid upgrade
        """
        subscription = self.get_subscription(subscription_id)
        if subscription is None:
            raise ValueError("Subscription not found")
        
        tier_order = [
            MonetizationTier.FREE,
            MonetizationTier.BASIC,
            MonetizationTier.PROFESSIONAL,
            MonetizationTier.ENTERPRISE,
        ]
        
        current_index = tier_order.index(subscription.tier)
        new_index = tier_order.index(new_tier)
        
        if new_index <= current_index:
            raise ValueError("Can only upgrade to higher tier")
        
        # Update subscription with new tier configuration
        tier_config = self._pricing_tiers[new_tier]
        subscription.tier = new_tier
        subscription.monthly_fee = tier_config["monthly_fee"]
        subscription.usage_rate = tier_config["usage_rate"]
        subscription.monthly_request_limit = tier_config["monthly_request_limit"]
        subscription.concurrent_agent_limit = tier_config["concurrent_agent_limit"]
        subscription.api_rate_limit = tier_config["api_rate_limit"]
        subscription.enabled_agents = tier_config["enabled_agents"]
        subscription.premium_features = tier_config["premium_features"]
        
        return subscription


# Global subscription manager instance
subscription_manager = SubscriptionManager()