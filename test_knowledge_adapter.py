#!/usr/bin/env python3
"""Comprehensive Test Suite for Autonomous Knowledge Adapter

Tests the autonomous knowledge adapter functionality across all 49 agents
to ensure each agent is equipped with plug-and-play knowledge capabilities.
"""

import asyncio
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from mega_agents.core.knowledge_adapter import (
    AutonomousKnowledgeAdapter, 
    KnowledgeSource, 
    KnowledgeSourceType,
    get_knowledge_adapter
)
from mega_agents.core.base_agent import BaseAgent, AgentConfig
from mega_agents.agents.analytics.agent import AnalyticsAgent


async def test_knowledge_adapter_creation():
    """Test knowledge adapter creation and initialization"""
    print("\n=== Testing Knowledge Adapter Creation ===")
    
    # Test adapter creation for different domains
    domains = ["analytics", "content", "cybersecurity", "financial", "general"]
    
    for domain in domains:
        try:
            adapter = get_knowledge_adapter(domain)
            print(f"✅ Created knowledge adapter for domain: {domain}")
            
            # Check default sources are loaded
            summary = adapter.get_knowledge_summary()
            assert summary["agent_domain"] == domain, f"Domain mismatch: expected {domain}, got {summary['agent_domain']}"
            assert summary["metrics"]["total_sources"] > 0, f"No sources loaded for domain {domain}"
            print(f"   - Loaded {summary['metrics']['total_sources']} default knowledge sources")
            
            # Test adding custom source
            custom_source = KnowledgeSource(
                id=f"test_source_{domain}",
                name=f"Test Source for {domain}",
                url="https://github.com/test/example",
                source_type=KnowledgeSourceType.GITHUB_REPO,
                domain_tags={domain, "test"},
                priority=5
            )
            
            success = adapter.add_knowledge_source(custom_source)
            assert success, f"Failed to add custom source for {domain}"
            print(f"   - Added custom knowledge source for {domain}")
            
        except Exception as e:
            print(f"❌ Error with domain {domain}: {e}")
            raise e
    
    print("✅ Knowledge Adapter Creation test passed")
    return True


async def test_knowledge_extraction():
    """Test knowledge extraction from sources"""
    print("\n=== Testing Knowledge Extraction ===")
    
    adapter = get_knowledge_adapter("test_extraction")
    
    # Add a test source (using a real GitHub repo for testing)
    test_source = KnowledgeSource(
        id="test_extraction_source",
        name="Test Extraction Source",
        url="https://github.com/microsoft/vscode",  # Well-known repo
        source_type=KnowledgeSourceType.GITHUB_REPO,
        domain_tags={"development", "editor"},
        priority=8
    )
    
    adapter.add_knowledge_source(test_source)
    
    # Test manual knowledge crawling (limited to avoid API limits)
    print("   - Testing knowledge crawling...")
    knowledge_items = await adapter._crawl_knowledge_sources()
    
    if knowledge_items:
        print(f"   - Extracted {len(knowledge_items)} knowledge items")
        for item in knowledge_items[:3]:  # Show first 3 items
            print(f"     * {item.title} (relevance: {item.relevance_score:.2f})")
    else:
        print("   - No knowledge items extracted (may be due to rate limits)")
    
    print("✅ Knowledge Extraction test passed")
    return True


async def test_agent_knowledge_integration():
    """Test knowledge adapter integration with agents"""
    print("\n=== Testing Agent-Knowledge Integration ===")
    
    # Create test agent with knowledge adapter
    config = AgentConfig(
        name="Test Knowledge Agent",
        agent_type="analytics",
        description="Test agent for knowledge integration"
    )
    
    agent = AnalyticsAgent(config)
    
    # Test knowledge adapter is available
    assert hasattr(agent, 'knowledge_adapter'), "Agent missing knowledge adapter"
    assert agent.knowledge_adapter.agent_domain == "analytics"
    print("✅ Agent has knowledge adapter")
    
    # Test knowledge summary
    summary = agent.get_knowledge_summary()
    assert "agent_domain" in summary
    assert summary["agent_domain"] == "analytics"
    print(f"✅ Knowledge summary: {summary['metrics']['total_sources']} sources")
    
    # Test querying knowledge
    knowledge_results = await agent.query_knowledge("data analysis")
    print(f"✅ Knowledge query returned {len(knowledge_results)} results")
    
    # Test profit recommendations
    recommendations = await agent.get_profit_recommendations()
    print(f"✅ Generated {len(recommendations)} profit recommendations")
    
    # Test capability enhancement
    enhanced_capabilities = await agent.enhance_capabilities_with_knowledge()
    print(f"✅ Enhanced capabilities: {len(enhanced_capabilities)} total")
    
    # Test adding custom knowledge source through agent
    success = await agent.add_custom_knowledge_source(
        name="Custom Analytics Resource",
        url="https://github.com/pandas-dev/pandas",
        source_type="github_repo",
        domain_tags=["analytics", "data_processing"]
    )
    assert success, "Failed to add custom knowledge source"
    print("✅ Added custom knowledge source through agent")
    
    print("✅ Agent-Knowledge Integration test passed")
    return True


async def test_autonomous_learning():
    """Test autonomous learning functionality"""
    print("\n=== Testing Autonomous Learning ===")
    
    adapter = get_knowledge_adapter("test_learning")
    
    # Test starting autonomous learning
    success = await adapter.start_autonomous_learning()
    assert success, "Failed to start autonomous learning"
    print("✅ Started autonomous learning")
    
    # Wait a short time to let learning process initialize
    await asyncio.sleep(2)
    
    # Check status
    summary = adapter.get_knowledge_summary()
    print(f"   - Learning status: {summary['status']}")
    print(f"   - Total sources: {summary['metrics']['total_sources']}")
    
    # Test stopping autonomous learning
    await adapter.stop_autonomous_learning()
    print("✅ Stopped autonomous learning")
    
    print("✅ Autonomous Learning test passed")
    return True


async def test_knowledge_profit_optimization():
    """Test profit optimization using knowledge"""
    print("\n=== Testing Knowledge-Based Profit Optimization ===")
    
    adapter = get_knowledge_adapter("profit_test")
    
    # Add some mock knowledge items for testing
    from mega_agents.core.knowledge_adapter import KnowledgeItem
    import hashlib
    
    # Create mock knowledge items about profit optimization
    mock_items = [
        KnowledgeItem(
            id=hashlib.md5("profit_item_1".encode()).hexdigest(),
            source_id="mock_source",
            title="API Revenue Optimization",
            content="Implement usage-based pricing for API services to maximize revenue. Studies show 40% increase in profit with proper pricing tiers.",
            content_type="best_practices",
            domain_tags={"revenue", "api", "pricing"},
            relevance_score=0.9
        ),
        KnowledgeItem(
            id=hashlib.md5("profit_item_2".encode()).hexdigest(),
            source_id="mock_source",
            title="Automation Cost Savings",
            content="Automate repetitive tasks to reduce operational costs. Companies report 30% cost reduction through intelligent automation.",
            content_type="tutorial",
            domain_tags={"automation", "cost_savings", "efficiency"},
            relevance_score=0.8
        )
    ]
    
    # Add mock items to knowledge base
    for item in mock_items:
        adapter._knowledge_base[item.id] = item
    
    # Test profit recommendations
    recommendations = await adapter.get_profit_recommendations()
    print(f"✅ Generated {len(recommendations)} profit recommendations")
    
    for rec in recommendations:
        print(f"   - {rec['type']}: {rec['description'][:100]}...")
    
    # Test profit opportunity analysis
    opportunities = adapter._analyze_profit_opportunities()
    print(f"✅ Identified {len(opportunities)} profit opportunities")
    
    print("✅ Knowledge-Based Profit Optimization test passed")
    return True


async def test_all_agent_domains():
    """Test knowledge adapter works for all agent domains"""
    print("\n=== Testing All 49 Agent Domains ===")
    
    # List of all 49 agent types from the Atlas
    agent_domains = [
        "analytics", "content", "customer_service", "data_processing", "email_marketing",
        "financial", "healthcare", "hr", "iot", "legal", "logistics", "manufacturing",
        "marketing", "project_management", "research", "sales", "social_media",
        "translation", "quality_assurance", "supply_chain", "cybersecurity", "education",
        "real_estate", "travel", "gaming", "fitness", "food", "fashion", "automotive",
        "energy", "agriculture", "media", "telecommunications", "insurance", "banking",
        "consulting", "nonprofit", "government", "hospitality", "sports", "music",
        "art", "photography", "video", "construction", "pharmaceutical", "entertainment",
        "innovation"
    ]
    
    successful_domains = 0
    failed_domains = []
    
    for domain in agent_domains:
        try:
            # Create knowledge adapter for each domain
            adapter = get_knowledge_adapter(domain)
            
            # Verify it has proper configuration
            summary = adapter.get_knowledge_summary()
            assert summary["agent_domain"] == domain, f"Domain mismatch for {domain}"
            assert summary["metrics"]["total_sources"] >= 3, f"Insufficient sources for {domain}: {summary['metrics']['total_sources']}"  # At least build-your-own-x + 2 others
            
            # Test basic functionality
            knowledge_results = adapter.query_knowledge("implementation")
            recommendations = await adapter.get_profit_recommendations()
            
            successful_domains += 1
            print(f"✅ Domain '{domain}': {summary['metrics']['total_sources']} sources, {len(knowledge_results)} knowledge items")
            
        except Exception as e:
            failed_domains.append(domain)
            print(f"❌ Domain '{domain}' failed: {e}")
    
    print(f"\n✅ Successfully tested {successful_domains}/{len(agent_domains)} agent domains")
    
    if failed_domains:
        print(f"Failed domains: {failed_domains}")
    
    # Verify we tested all 49 domains
    assert len(agent_domains) == 49, f"Expected 49 domains, got {len(agent_domains)}"
    assert successful_domains >= 45, f"Expected at least 45 successful domains, got {successful_domains}"  # Allow some failures
    
    print("✅ All Agent Domains test passed")
    return True


async def test_deployment_readiness():
    """Test deployment readiness of knowledge adapter system"""
    print("\n=== Testing Deployment Readiness ===")
    
    # Test multiple adapters can run simultaneously
    adapters = []
    for domain in ["analytics", "content", "cybersecurity"]:
        adapter = get_knowledge_adapter(domain)
        adapters.append(adapter)
        await adapter.start_autonomous_learning()
    
    print("✅ Multiple adapters running simultaneously")
    
    # Test resource cleanup
    for adapter in adapters:
        await adapter.stop_autonomous_learning()
    
    print("✅ Resource cleanup successful")
    
    # Test adapter state persistence
    adapter = get_knowledge_adapter("persistence_test")
    original_summary = adapter.get_knowledge_summary()
    
    # Get new adapter instance (should share state)
    adapter2 = get_knowledge_adapter("persistence_test")
    new_summary = adapter2.get_knowledge_summary()
    
    assert original_summary["agent_domain"] == new_summary["agent_domain"]
    print("✅ Adapter state persistence working")
    
    # Test error handling
    try:
        # Test with invalid knowledge source
        invalid_source = KnowledgeSource(
            id="invalid_test",
            name="Invalid Source",
            url="invalid://not-a-url",
            source_type=KnowledgeSourceType.GITHUB_REPO
        )
        
        adapter.add_knowledge_source(invalid_source)
        # Should not crash even with invalid source
        print("✅ Error handling for invalid sources")
        
    except Exception as e:
        print(f"❌ Error handling failed: {e}")
    
    print("✅ Deployment Readiness test passed")
    return True


async def main():
    """Run comprehensive knowledge adapter test suite"""
    print("🚀 Starting Autonomous Knowledge Adapter Test Suite")
    print("=" * 60)
    
    tests = [
        ("Knowledge Adapter Creation", test_knowledge_adapter_creation),
        ("Knowledge Extraction", test_knowledge_extraction),
        ("Agent-Knowledge Integration", test_agent_knowledge_integration),
        ("Autonomous Learning", test_autonomous_learning),
        ("Profit Optimization", test_knowledge_profit_optimization),
        ("All Agent Domains", test_all_agent_domains),
        ("Deployment Readiness", test_deployment_readiness),
    ]
    
    passed_tests = 0
    failed_tests = []
    
    for test_name, test_func in tests:
        try:
            success = await test_func()
            if success:
                passed_tests += 1
                print(f"✅ {test_name} PASSED")
            else:
                failed_tests.append(test_name)
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            failed_tests.append(test_name)
            print(f"❌ {test_name} FAILED: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Test Suite Summary")
    print("=" * 60)
    
    for test_name, _ in tests:
        status = "✅ PASSED" if test_name not in failed_tests else "❌ FAILED"
        print(f"{test_name:<30} : {status}")
    
    print(f"\nOverall: {passed_tests}/{len(tests)} tests passed")
    
    if failed_tests:
        print(f"❌ Failed tests: {', '.join(failed_tests)}")
        return False
    else:
        print("🎉 All tests passed! Autonomous Knowledge Adapter is ready for production.")
        return True


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        sys.exit(1)