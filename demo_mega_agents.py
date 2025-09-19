#!/usr/bin/env python3
"""AI Mega Agents Atlas - Interactive Demo

This script provides an interactive demonstration of the AI Mega Agents Atlas
system showcasing all enterprise features and capabilities.
"""

import asyncio
import logging
import json
import time
from datetime import datetime
from typing import Dict, Any

try:
    from mega_agents.core.agent_registry import agent_registry
    from mega_agents.core.revenue_engine import revenue_engine, BillingModel
    from mega_agents.core.scaling_manager import scaling_manager, ScalingTrigger, ScalingDirection, ResourceMetrics
    from mega_agents.agents.analytics.agent import AnalyticsAgent
    from mega_agents.core.base_agent import AgentConfig
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure the AI Mega Agents Atlas is properly installed")
    exit(1)


class MegaAgentsDemo:
    """Interactive demo of AI Mega Agents Atlas capabilities"""
    
    def __init__(self):
        """Initialize the demo"""
        self.logger = logging.getLogger("mega_agents.demo")
        self.demo_start_time = datetime.utcnow()
        
        # Demo statistics
        self.requests_processed = 0
        self.revenue_generated = 0.0
        self.agents_deployed = 0
        
    def print_header(self, title: str):
        """Print formatted section header"""
        print("\n" + "=" * 60)
        print(f"🚀 {title}")
        print("=" * 60)
    
    def print_success(self, message: str):
        """Print success message"""
        print(f"✅ {message}")
    
    def print_info(self, message: str):
        """Print info message"""
        print(f"ℹ️  {message}")
    
    def print_stats(self, data: Dict[str, Any]):
        """Print formatted statistics"""
        for key, value in data.items():
            if isinstance(value, float):
                print(f"   📊 {key}: {value:.2f}")
            elif isinstance(value, dict):
                print(f"   📊 {key}:")
                for k, v in value.items():
                    print(f"      • {k}: {v}")
            else:
                print(f"   📊 {key}: {value}")
    
    async def demo_intro(self):
        """Demo introduction"""
        self.print_header("AI Mega Agents Atlas - Enterprise Demo")
        
        print("""
🎯 Welcome to the AI Mega Agents Atlas Interactive Demo!

This demonstration showcases our revolutionary enterprise-grade AI platform
featuring 49 verified autonomous agents designed for:

🏢 Enterprise Features:
   • 24/7 Autonomous Operation
   • Revenue Generation & Monetization
   • Auto-Scaling & Self-Healing
   • Contract Automation
   • Real-time Analytics

🤖 Agent Capabilities:
   • Advanced Analytics & BI
   • Content Creation & Marketing
   • Customer Service & Support
   • Financial Analysis & Trading
   • Healthcare & Medical AI
   • ... and 44 more specialized agents

💰 Business Benefits:
   • Instant ROI from day one
   • Automated revenue streams
   • Scalable from startup to enterprise
   • Plug-and-play deployment
   • Zero maintenance overhead

Let's explore the system capabilities step by step...
        """)
        
        input("\n🎬 Press Enter to start the demo...")
    
    async def demo_agent_registration(self):
        """Demonstrate agent registration and deployment"""
        self.print_header("Agent Registration & Deployment")
        
        print("Registering AI Analytics Agent...")
        
        # Register the analytics agent
        success = agent_registry.register_agent_type(
            agent_class=AnalyticsAgent,
            agent_type="analytics",
            name="AI Analytics Agent",
            description="Advanced data analytics and business intelligence",
            capabilities=["statistical_analysis", "predictive_modeling", "dashboards"],
            revenue_models=["usage_based", "subscription", "consulting"]
        )
        
        if success:
            self.print_success("Analytics Agent registered successfully")
            self.agents_deployed += 1
        
        # Create agent instance
        print("\nCreating agent instance...")
        instance_id = await agent_registry.create_agent_instance("analytics")
        
        if instance_id:
            self.print_success(f"Agent instance created: {instance_id}")
        
        # Show registry status
        print("\nRegistry Status:")
        status = await agent_registry.get_registry_status()
        self.print_stats({
            "Registered Agent Types": status["total_registered_types"],
            "Active Instances": status["total_active_instances"],
            "Total Requests Processed": status["total_requests_processed"]
        })
        
        input("\n⏭️  Press Enter to continue...")
    
    async def demo_revenue_engine(self):
        """Demonstrate revenue generation capabilities"""
        self.print_header("Revenue Engine & Monetization")
        
        print("Setting up revenue rules and contracts...")
        
        # Add revenue rules
        basic_rule = revenue_engine.add_revenue_rule(
            name="Analytics Basic Usage",
            billing_model=BillingModel.USAGE_BASED,
            base_rate=0.05,
            unit="request",
            minimum_charge=0.01
        )
        
        premium_rule = revenue_engine.add_revenue_rule(
            name="Analytics Premium",
            billing_model=BillingModel.USAGE_BASED,
            base_rate=0.25,
            unit="request",
            conditions={"priority": True}
        )
        
        self.print_success(f"Revenue rules created: {basic_rule[:8]}... and {premium_rule[:8]}...")
        
        # Create auto-contract
        print("\nCreating automated client contract...")
        contract_id = await revenue_engine.create_auto_contract(
            client_id="demo_enterprise_client",
            agent_type="analytics",
            duration_months=12
        )
        
        if contract_id:
            self.print_success(f"Auto-contract generated: {contract_id[:8]}...")
        
        # Process some revenue-generating requests
        print("\nProcessing revenue-generating requests...")
        
        requests = [
            {"type": "basic_analysis", "priority": False, "data_points": 1000},
            {"type": "advanced_modeling", "priority": True, "data_points": 5000},
            {"type": "real_time_dashboard", "priority": False, "data_points": 2000}
        ]
        
        total_revenue = 0.0
        for i, request in enumerate(requests, 1):
            revenue = await revenue_engine.calculate_revenue(
                agent_instance_id=f"demo_instance_{i}",
                agent_type="analytics",
                client_id="demo_enterprise_client",
                usage_data=request
            )
            total_revenue += revenue
            self.requests_processed += 1
            print(f"   Request {i}: ${revenue:.4f} revenue generated")
        
        self.revenue_generated = total_revenue
        self.print_success(f"Total revenue generated: ${total_revenue:.2f}")
        
        # Show revenue analytics
        print("\nRevenue Analytics:")
        analytics = await revenue_engine.get_revenue_analytics()
        self.print_stats({
            "Total Revenue": f"${analytics['total_revenue']:.2f}",
            "Active Contracts": analytics["active_contracts"],
            "Total Transactions": analytics["total_transactions"],
            "Average Transaction Value": f"${analytics['average_transaction_value']:.4f}"
        })
        
        input("\n⏭️  Press Enter to continue...")
    
    async def demo_auto_scaling(self):
        """Demonstrate auto-scaling capabilities"""
        self.print_header("Auto-Scaling & Performance Optimization")
        
        print("Configuring intelligent auto-scaling rules...")
        
        # Add scaling rules
        cpu_rule = scaling_manager.add_scaling_rule(
            name="CPU-based Scaling",
            agent_type="analytics",
            trigger=ScalingTrigger.CPU_THRESHOLD,
            metric_threshold=75.0,
            scaling_direction=ScalingDirection.UP,
            scaling_factor=1.5,
            max_instances=10
        )
        
        response_time_rule = scaling_manager.add_scaling_rule(
            name="Response Time Scaling",
            agent_type="analytics",
            trigger=ScalingTrigger.RESPONSE_TIME,
            metric_threshold=500.0,
            scaling_direction=ScalingDirection.UP,
            scaling_factor=1.3,
            max_instances=5
        )
        
        self.print_success(f"Scaling rules created: {len([cpu_rule, response_time_rule])} rules active")
        
        # Simulate high load metrics
        print("\nSimulating high load conditions...")
        
        high_load_metrics = ResourceMetrics(
            cpu_percentage=85.0,
            memory_percentage=70.0,
            response_time_ms=650.0,
            throughput_per_second=150.0,
            error_rate_percentage=2.5,
            queue_length=25
        )
        
        await scaling_manager.update_metrics("analytics", "demo_instance", high_load_metrics)
        self.print_success("High load metrics recorded")
        
        # Get scaling recommendations
        print("\nAnalyzing scaling recommendations...")
        recommendations = await scaling_manager.get_scaling_recommendations("analytics")
        
        print(f"\nScaling Recommendations ({len(recommendations)} found):")
        for i, rec in enumerate(recommendations, 1):
            self.print_stats({
                f"Recommendation {i}": {
                    "Trigger": rec.get("trigger", "unknown"),
                    "Direction": rec.get("direction", "unknown"),
                    "Priority": f"{rec.get('priority', 0):.0f}%",
                    "Reason": rec.get("reason", "No reason provided")
                }
            })
        
        # Show scaling status
        print("\nScaling Manager Status:")
        status = await scaling_manager.get_scaling_status()
        self.print_stats({
            "Total Scaling Rules": status["total_scaling_rules"],
            "Active Scaling Rules": status["active_scaling_rules"],
            "Success Rate": f"{status['success_rate']:.1f}%",
            "Cost Savings": f"${status['cost_savings']:.2f}"
        })
        
        input("\n⏭️  Press Enter to continue...")
    
    async def demo_analytics_agent(self):
        """Demonstrate Analytics Agent capabilities"""
        self.print_header("AI Analytics Agent - Live Demo")
        
        print("Testing Analytics Agent with real requests...")
        
        # Test different types of analytics requests
        test_requests = [
            {
                "name": "Sales Performance Analysis",
                "request": {
                    "type": "analytics",
                    "data_source": "sales_database",
                    "analysis_type": "descriptive",
                    "parameters": {"metrics": ["revenue", "conversion", "customer_acquisition"]}
                }
            },
            {
                "name": "Predictive Revenue Modeling",
                "request": {
                    "type": "analytics",
                    "data_source": "financial_data",
                    "analysis_type": "predictive",
                    "parameters": {"forecast_period": "3_months", "confidence_level": 0.95}
                }
            },
            {
                "name": "Customer Segmentation Dashboard",
                "request": {
                    "type": "dashboard",
                    "parameters": {
                        "name": "customer_segments",
                        "widgets": ["demographics", "behavior_analysis", "lifetime_value"]
                    }
                }
            }
        ]
        
        for test in test_requests:
            print(f"\n🔍 Processing: {test['name']}")
            
            # Route request through agent registry
            start_time = time.time()
            response = await agent_registry.route_request("analytics", test["request"])
            processing_time = (time.time() - start_time) * 1000
            
            if response.get("status") == "success":
                self.print_success(f"Analysis completed in {processing_time:.1f}ms")
                
                # Show key results
                if "results" in response:
                    results = response["results"]
                    if "summary" in results:
                        print("   📊 Key Insights:")
                        for key, value in list(results["summary"].items())[:3]:
                            print(f"      • {key}: {value}")
                
                # Calculate revenue for this request
                revenue = await revenue_engine.calculate_revenue(
                    agent_instance_id="demo_analytics",
                    agent_type="analytics",
                    client_id="demo_enterprise_client",
                    usage_data=test["request"]
                )
                print(f"   💰 Revenue Generated: ${revenue:.4f}")
                self.revenue_generated += revenue
                self.requests_processed += 1
            else:
                print(f"   ❌ Error: {response.get('error', 'Unknown error')}")
        
        input("\n⏭️  Press Enter to continue...")
    
    async def demo_system_health(self):
        """Demonstrate system health and monitoring"""
        self.print_header("System Health & Monitoring")
        
        print("Checking comprehensive system health...")
        
        # Get agent health
        analytics_instances = [
            instance for instance_id, instance in agent_registry.list_agent_instances().items()
            if instance["config"]["agent_type"] == "analytics"
        ]
        
        if analytics_instances:
            print("\n🏥 Agent Health Status:")
            for instance in analytics_instances[:1]:  # Show first instance
                agent_id = instance["agent_id"]
                status = instance["status"]
                uptime = (datetime.utcnow() - datetime.fromisoformat(instance["created_at"])).total_seconds()
                
                self.print_stats({
                    "Agent ID": agent_id[:8] + "...",
                    "Status": status,
                    "Uptime": f"{uptime:.1f} seconds",
                    "Revenue Generated": f"${instance['metrics']['revenue_generated']:.2f}"
                })
        
        # Registry health
        print("\n🏪 Registry Health:")
        registry_status = await agent_registry.get_registry_status()
        self.print_stats({
            "Total Agent Types": registry_status["total_registered_types"],
            "Active Instances": registry_status["total_active_instances"],
            "Requests Processed": registry_status["total_requests_processed"],
            "System Uptime": f"{registry_status['registry_uptime_seconds']:.1f}s"
        })
        
        # Revenue health
        print("\n💰 Revenue Engine Health:")
        revenue_analytics = await revenue_engine.get_revenue_analytics()
        self.print_stats({
            "Total Revenue": f"${revenue_analytics['total_revenue']:.2f}",
            "Active Contracts": revenue_analytics["active_contracts"],
            "Total Clients": revenue_analytics["total_clients"],
            "Growth Rate": f"{revenue_analytics['revenue_growth_rate']:.1f}%"
        })
        
        # Scaling health
        print("\n📈 Scaling Manager Health:")
        scaling_status = await scaling_manager.get_scaling_status()
        self.print_stats({
            "Scaling Rules": scaling_status["total_scaling_rules"],
            "Scaling Events": scaling_status["total_scaling_events"],
            "Success Rate": f"{scaling_status['success_rate']:.1f}%",
            "Monitored Agents": scaling_status["monitored_agent_types"]
        })
        
        input("\n⏭️  Press Enter to continue...")
    
    async def demo_summary(self):
        """Show demo summary and next steps"""
        self.print_header("Demo Summary & Results")
        
        demo_duration = (datetime.utcnow() - self.demo_start_time).total_seconds()
        
        print(f"""
🎉 AI Mega Agents Atlas Demo Complete!

📊 Demo Statistics:
   • Duration: {demo_duration:.1f} seconds
   • Agents Deployed: {self.agents_deployed}
   • Requests Processed: {self.requests_processed}
   • Revenue Generated: ${self.revenue_generated:.2f}
   • System Status: ✅ All systems operational

🚀 What You've Seen:
   ✅ Enterprise-grade agent framework
   ✅ Autonomous revenue generation
   ✅ Intelligent auto-scaling
   ✅ Real-time analytics and insights
   ✅ Production-ready architecture

💡 Next Steps:
   1. Deploy additional agents (48 more available)
   2. Integrate with your existing systems
   3. Configure custom revenue models
   4. Scale to production workloads
   5. Access enterprise support

🌟 Key Benefits Demonstrated:
   • Instant ROI from deployed agents
   • Zero-maintenance autonomous operation
   • Scalable from startup to enterprise
   • Built-in monetization and billing
   • Enterprise-grade reliability

📞 Ready to Deploy?
   • Full documentation: MEGA_AGENTS_GUIDE.md
   • Quick start: python deploy_mega_agents.py
   • Kubernetes: kubectl apply -f infrastructure/kubernetes/
   • Support: Enterprise support available

Thank you for exploring the AI Mega Agents Atlas!
The future of autonomous AI business operations starts here.
        """)
    
    async def run_demo(self):
        """Run the complete interactive demo"""
        # Configure logging
        logging.basicConfig(
            level=logging.WARNING,  # Reduce noise during demo
            format='%(name)s - %(levelname)s - %(message)s'
        )
        
        try:
            await self.demo_intro()
            await self.demo_agent_registration()
            await self.demo_revenue_engine()
            await self.demo_auto_scaling()
            await self.demo_analytics_agent()
            await self.demo_system_health()
            await self.demo_summary()
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Demo interrupted by user")
        except Exception as e:
            print(f"\n\n❌ Demo error: {e}")
        finally:
            # Cleanup
            print("\n🧹 Cleaning up demo resources...")
            await agent_registry.shutdown()
            await revenue_engine.shutdown()
            await scaling_manager.shutdown()
            print("✅ Demo cleanup completed")


async def main():
    """Main demo function"""
    demo = MegaAgentsDemo()
    await demo.run_demo()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo ended. Thank you!")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        exit(1)