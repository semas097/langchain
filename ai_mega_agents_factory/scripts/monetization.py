"""
AI Mega Agents Factory - Monetization Service

Handles subscription management, billing, and usage tracking for the AI agents platform.
Integrates with popular payment processors and provides flexible pricing models.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json

from ai_mega_agents_factory import AgentTier, monetization_service


class PaymentProvider(str, Enum):
    """Supported payment providers"""
    STRIPE = "stripe"
    PAYPAL = "paypal"
    SQUARE = "square"
    MOCK = "mock"  # For testing


@dataclass
class Subscription:
    """User subscription model"""
    user_id: str
    tier: AgentTier
    start_date: datetime
    end_date: datetime
    auto_renew: bool = True
    payment_method: str = ""
    status: str = "active"


@dataclass
class Usage:
    """Usage tracking model"""
    user_id: str
    agent_type: str
    operation: str
    count: int
    timestamp: datetime
    cost: float


class SubscriptionManager:
    """Manages user subscriptions and billing"""
    
    def __init__(self, payment_provider: PaymentProvider = PaymentProvider.MOCK):
        self.payment_provider = payment_provider
        self.subscriptions: Dict[str, Subscription] = {}
        self.usage_history: List[Usage] = []
        
        # Pricing tiers (per operation)
        self.pricing = {
            AgentTier.FREE: {
                "monthly_fee": 0.0,
                "operation_costs": {
                    "data_analysis": 0.0,
                    "email": 0.0,
                    "document_processing": 0.0
                },
                "limits": {
                    "data_analysis": 10,
                    "email": 5,
                    "document_processing": 5
                }
            },
            AgentTier.BASIC: {
                "monthly_fee": 29.99,
                "operation_costs": {
                    "data_analysis": 0.01,
                    "email": 0.02,
                    "document_processing": 0.03
                },
                "limits": {
                    "data_analysis": 1000,
                    "email": 500,
                    "document_processing": 200
                }
            },
            AgentTier.PREMIUM: {
                "monthly_fee": 99.99,
                "operation_costs": {
                    "data_analysis": 0.005,
                    "email": 0.01,
                    "document_processing": 0.015
                },
                "limits": {
                    "data_analysis": 10000,
                    "email": 5000,
                    "document_processing": 2000
                }
            },
            AgentTier.ENTERPRISE: {
                "monthly_fee": 499.99,
                "operation_costs": {
                    "data_analysis": 0.001,
                    "email": 0.005,
                    "document_processing": 0.01
                },
                "limits": {
                    "data_analysis": -1,  # Unlimited
                    "email": -1,
                    "document_processing": -1
                }
            }
        }
    
    def create_subscription(self, user_id: str, tier: AgentTier, 
                          payment_method: str = "") -> bool:
        """Create a new subscription"""
        try:
            # Mock payment processing
            if self._process_payment(user_id, tier, payment_method):
                subscription = Subscription(
                    user_id=user_id,
                    tier=tier,
                    start_date=datetime.utcnow(),
                    end_date=datetime.utcnow() + timedelta(days=30),
                    payment_method=payment_method
                )
                self.subscriptions[user_id] = subscription
                return True
            return False
        except Exception as e:
            print(f"Subscription creation failed: {e}")
            return False
    
    def upgrade_subscription(self, user_id: str, new_tier: AgentTier) -> bool:
        """Upgrade user subscription"""
        if user_id not in self.subscriptions:
            return self.create_subscription(user_id, new_tier)
        
        subscription = self.subscriptions[user_id]
        old_tier = subscription.tier
        
        # Calculate prorated charge
        prorated_cost = self._calculate_prorated_cost(subscription, new_tier)
        
        if self._process_payment(user_id, new_tier, subscription.payment_method, prorated_cost):
            subscription.tier = new_tier
            return True
        return False
    
    def check_usage_limits(self, user_id: str, agent_type: str) -> bool:
        """Check if user has exceeded usage limits"""
        if user_id not in self.subscriptions:
            return False
        
        subscription = self.subscriptions[user_id]
        tier_limits = self.pricing[subscription.tier]["limits"]
        
        if agent_type not in tier_limits:
            return False
        
        limit = tier_limits[agent_type]
        if limit == -1:  # Unlimited
            return True
        
        # Count current month usage
        current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_usage = sum(
            usage.count for usage in self.usage_history
            if (usage.user_id == user_id and 
                usage.agent_type == agent_type and 
                usage.timestamp >= current_month_start)
        )
        
        return current_usage < limit
    
    def track_usage(self, user_id: str, agent_type: str, operation: str) -> float:
        """Track usage and calculate cost"""
        if user_id not in self.subscriptions:
            return 0.0
        
        subscription = self.subscriptions[user_id]
        operation_cost = self.pricing[subscription.tier]["operation_costs"].get(agent_type, 0.0)
        
        usage = Usage(
            user_id=user_id,
            agent_type=agent_type,
            operation=operation,
            count=1,
            timestamp=datetime.utcnow(),
            cost=operation_cost
        )
        
        self.usage_history.append(usage)
        return operation_cost
    
    def generate_invoice(self, user_id: str, month: int, year: int) -> Dict[str, Any]:
        """Generate monthly invoice"""
        if user_id not in self.subscriptions:
            return {}
        
        subscription = self.subscriptions[user_id]
        month_start = datetime(year, month, 1)
        month_end = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
        
        # Base subscription fee
        monthly_fee = self.pricing[subscription.tier]["monthly_fee"]
        
        # Usage charges
        usage_charges = {}
        total_usage_cost = 0.0
        
        for usage in self.usage_history:
            if (usage.user_id == user_id and 
                month_start <= usage.timestamp < month_end):
                
                if usage.agent_type not in usage_charges:
                    usage_charges[usage.agent_type] = {"count": 0, "cost": 0.0}
                
                usage_charges[usage.agent_type]["count"] += usage.count
                usage_charges[usage.agent_type]["cost"] += usage.cost
                total_usage_cost += usage.cost
        
        return {
            "user_id": user_id,
            "month": month,
            "year": year,
            "tier": subscription.tier.value,
            "base_fee": monthly_fee,
            "usage_charges": usage_charges,
            "total_usage_cost": total_usage_cost,
            "total_amount": monthly_fee + total_usage_cost,
            "currency": "USD"
        }
    
    def _process_payment(self, user_id: str, tier: AgentTier, 
                        payment_method: str, amount: Optional[float] = None) -> bool:
        """Process payment through payment provider"""
        if amount is None:
            amount = self.pricing[tier]["monthly_fee"]
        
        if self.payment_provider == PaymentProvider.MOCK:
            # Mock successful payment
            print(f"Mock payment processed: ${amount} for user {user_id}")
            return True
        
        # Integration with real payment processors would go here
        # For example, Stripe integration:
        # stripe.Charge.create(amount=int(amount * 100), currency='usd', ...)
        
        return True
    
    def _calculate_prorated_cost(self, subscription: Subscription, new_tier: AgentTier) -> float:
        """Calculate prorated cost for tier upgrade"""
        days_remaining = (subscription.end_date - datetime.utcnow()).days
        old_daily_rate = self.pricing[subscription.tier]["monthly_fee"] / 30
        new_daily_rate = self.pricing[new_tier]["monthly_fee"] / 30
        
        return (new_daily_rate - old_daily_rate) * days_remaining


# Sample usage and testing
async def demo_monetization():
    """Demonstrate monetization features"""
    manager = SubscriptionManager()
    
    # Create subscriptions for demo users
    users = [
        ("user_1", AgentTier.FREE),
        ("user_2", AgentTier.BASIC),
        ("user_3", AgentTier.PREMIUM)
    ]
    
    for user_id, tier in users:
        success = manager.create_subscription(user_id, tier, "card_123")
        print(f"Created {tier.value} subscription for {user_id}: {success}")
    
    # Simulate usage
    for user_id, _ in users:
        for _ in range(5):
            cost = manager.track_usage(user_id, "data_analysis", "analysis")
            print(f"Usage tracked for {user_id}: ${cost}")
    
    # Check limits
    for user_id, _ in users:
        can_use = manager.check_usage_limits(user_id, "data_analysis")
        print(f"User {user_id} can use data analysis: {can_use}")
    
    # Generate invoices
    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year
    
    for user_id, _ in users:
        invoice = manager.generate_invoice(user_id, current_month, current_year)
        print(f"Invoice for {user_id}: ${invoice.get('total_amount', 0)}")
    
    # Upgrade subscription
    success = manager.upgrade_subscription("user_1", AgentTier.BASIC)
    print(f"Upgraded user_1 to BASIC: {success}")


if __name__ == "__main__":
    asyncio.run(demo_monetization())