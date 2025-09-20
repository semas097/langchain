#!/usr/bin/env python3
"""AI Mega Agents Atlas - Simple Test Script

This script demonstrates the basic functionality of the AI Mega Agents Atlas system.
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from mega_agents.core.base_agent import BaseAgent, AgentConfig, AgentStatus
    from mega_agents.core.agent_registry import agent_registry
    from mega_agents.core.revenue_engine import revenue_engine, BillingModel
    from mega_agents.core.scaling_manager import scaling_manager, ScalingTrigger, ScalingDirection, ResourceMetrics
    from mega_agents.agents.analytics.agent import AnalyticsAgent
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all dependencies are installed")
    sys.exit(1)


async def test_analytics_agent():
    """Test the Analytics Agent functionality"""
    print("\n=== Testing Analytics Agent ===")
    
    # Create agent configuration
    config = AgentConfig(
        name="Test Analytics Agent",
        agent_type="analytics",
        description="Test analytics agent for validation"
    )
    
    # Create and start agent
    agent = AnalyticsAgent(config)
    success = await agent.start()
    
    if not success:
        print("❌ Failed to start Analytics Agent")
        return False
    
    print(f"✅ Analytics Agent started successfully (ID: {agent.agent_id})")
    
    # Test health check
    health = await agent.health_check()
    print(f"✅ Health check: {health['healthy']}")
    
    # Test analytics request
    test_request = {
        "type": "analytics",
        "data_source": "test_data",
        "analysis_type": "descriptive",
        "parameters": {"columns": ["revenue", "customers"]},
        "priority": False
    }
    
    response = await agent.process_request(test_request)
    print(f"✅ Analytics request processed: {response['status']}")
    
    # Test dashboard creation
    dashboard_request = {
        "type": "dashboard",
        "parameters": {
            "name": "test_dashboard",
            "widgets": ["revenue_chart", "customer_metrics"]
        }
    }
    
    dashboard_response = await agent.process_request(dashboard_request)
    print(f"✅ Dashboard created: {dashboard_response.get('dashboard_id', 'unknown')}")
    
    # Stop agent
    await agent.stop()
    print("✅ Analytics Agent stopped successfully")
    
    return True


async def test_agent_registry():
    """Test the Agent Registry functionality"""
    print("\n=== Testing Agent Registry ===")
    
    # Register Analytics Agent type
    success = agent_registry.register_agent_type(
        agent_class=AnalyticsAgent,
        agent_type="analytics",
        name="AI Analytics Agent",
        description="Advanced data analytics and business intelligence",
        capabilities=["statistical_analysis", "predictive_modeling"],
        revenue_models=["usage_based", "subscription"]
    )
    
    if not success:
        print("❌ Failed to register agent type")
        return False
    
    print("✅ Agent type registered successfully")
    
    # Create agent instance
    instance_id = await agent_registry.create_agent_instance("analytics")
    if not instance_id:
        print("❌ Failed to create agent instance")
        return False
    
    print(f"✅ Agent instance created: {instance_id}")
    
    # Route request to agent
    test_request = {
        "type": "analytics",
        "data_source": "registry_test",
        "analysis_type": "correlation"
    }
    
    response = await agent_registry.route_request("analytics", test_request)
    print(f"✅ Request routed successfully: {response.get('status', 'unknown')}")
    
    # Get registry status
    status = await agent_registry.get_registry_status()
    print(f"✅ Registry status - Active instances: {status['total_active_instances']}")
    
    # Cleanup
    await agent_registry.remove_agent_instance(instance_id)
    print("✅ Agent instance removed successfully")
    
    return True


async def test_revenue_engine():
    """Test the Revenue Engine functionality"""
    print("\n=== Testing Revenue Engine ===")
    
    # Add revenue rule
    rule_id = revenue_engine.add_revenue_rule(
        name="Test Analytics Rule",
        billing_model=BillingModel.USAGE_BASED,
        base_rate=0.05,
        unit="request"
    )
    
    print(f"✅ Revenue rule added: {rule_id}")
    
    # Create auto-contract
    contract_id = await revenue_engine.create_auto_contract(
        client_id="test_client",
        agent_type="analytics",
        duration_months=6
    )
    
    if contract_id:
        print(f"✅ Auto-contract created: {contract_id}")
    else:
        print("❌ Failed to create auto-contract")
        return False
    
    # Calculate revenue
    usage_data = {
        "request_type": "analytics",
        "analysis_type": "descriptive",
        "data_points": 1000,
        "priority": False
    }
    
    revenue = await revenue_engine.calculate_revenue(
        agent_instance_id="test_instance",
        agent_type="analytics",
        client_id="test_client",
        usage_data=usage_data
    )
    
    print(f"✅ Revenue calculated: ${revenue:.4f}")
    
    # Get revenue analytics
    analytics = await revenue_engine.get_revenue_analytics()
    print(f"✅ Revenue analytics - Total: ${analytics['total_revenue']:.2f}")
    
    return True


async def test_scaling_manager():
    """Test the Scaling Manager functionality"""
    print("\n=== Testing Scaling Manager ===")
    
    # Add scaling rule
    rule_id = scaling_manager.add_scaling_rule(
        name="Test CPU Scaling",
        agent_type="analytics",
        trigger=ScalingTrigger.CPU_THRESHOLD,
        metric_threshold=80.0,
        scaling_direction=ScalingDirection.UP,
        scaling_factor=1.5
    )
    
    print(f"✅ Scaling rule added: {rule_id}")
    
    # Update metrics
    metrics = ResourceMetrics(
        cpu_percentage=85.0,
        memory_percentage=60.0,
        response_time_ms=250.0,
        throughput_per_second=50.0
    )
    
    await scaling_manager.update_metrics("analytics", "test_instance", metrics)
    print("✅ Metrics updated successfully")
    
    # Get scaling recommendations
    recommendations = await scaling_manager.get_scaling_recommendations("analytics")
    print(f"✅ Scaling recommendations: {len(recommendations)} found")
    
    # Get scaling status
    status = await scaling_manager.get_scaling_status()
    print(f"✅ Scaling status - Rules: {status['total_scaling_rules']}")
    
    return True


async def run_comprehensive_test():
    """Run comprehensive test suite"""
    print("🚀 Starting AI Mega Agents Atlas Test Suite")
    print("=" * 50)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    test_results = []
    
    # Test individual components
    tests = [
        ("Analytics Agent", test_analytics_agent),
        ("Agent Registry", test_agent_registry),
        ("Revenue Engine", test_revenue_engine),
        ("Scaling Manager", test_scaling_manager)
    ]
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            test_results.append((test_name, result))
            if result:
                print(f"✅ {test_name} test passed")
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test error: {e}")
            test_results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 Test Suite Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20} : {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! AI Mega Agents Atlas is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False


async def main():
    """Main function"""
    try:
        success = await run_comprehensive_test()
        
        # Cleanup
        print("\n🧹 Cleaning up...")
        await agent_registry.shutdown()
        await revenue_engine.shutdown()
        await scaling_manager.shutdown()
        print("✅ Cleanup completed")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())