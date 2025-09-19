"""
AI Mega Agents Factory - Sample Usage Script

Demonstrates how to use the AI Mega Agents Factory with various agents.
Shows integration patterns, error handling, and best practices.
"""

import asyncio
import json
import time
from typing import Dict, Any

# Import the factory system
from ai_mega_agents_factory import (
    AgentConfig, AgentTier, agent_registry
)

# Import specific agents
from ai_mega_agents_factory.agents.data_analysis import DataAnalysisAgent, DataAnalysisConfig
from ai_mega_agents_factory.agents.email import EmailAgent, EmailConfig
from ai_mega_agents_factory.agents.document_processing import DocumentProcessingAgent, DocumentConfig


async def demo_data_analysis():
    """Demonstrate data analysis agent"""
    print("=== Data Analysis Agent Demo ===")
    
    # Create agent configuration
    config = DataAnalysisConfig(
        name="Analytics Agent 1",
        description="Demo data analysis agent",
        tier=AgentTier.BASIC,
        max_rows=50000
    )
    
    # Create agent instance
    agent = await agent_registry.create_agent("data_analysis", config)
    if not agent:
        print("Failed to create data analysis agent")
        return
    
    print(f"Created agent: {agent.config.name}")
    print(f"Agent status: {agent.get_status()}")
    
    # Sample CSV data
    sample_data = """name,age,salary,department
John,25,50000,Engineering
Jane,30,60000,Marketing
Bob,35,70000,Engineering
Alice,28,55000,Marketing
Charlie,32,65000,Sales"""
    
    # Test different analysis types
    analysis_tasks = [
        {"data": sample_data, "analysis_type": "summary"},
        {"data": sample_data, "analysis_type": "correlation"},
        {"data": sample_data, "analysis_type": "outliers"}
    ]
    
    for task in analysis_tasks:
        print(f"\nRunning {task['analysis_type']} analysis...")
        result = await agent.execute(task)
        
        if result.success:
            print(f"Analysis completed in {result.execution_time:.2f}s")
            print(f"Result: {result.data['result'][:200]}...")
        else:
            print(f"Analysis failed: {result.error}")
    
    # Stop the agent
    await agent_registry.stop_agent(agent.config.agent_id)
    print("Data analysis agent stopped")


async def demo_email_agent():
    """Demonstrate email agent"""
    print("\n=== Email Agent Demo ===")
    
    # Create agent configuration
    config = EmailConfig(
        name="Email Agent 1",
        description="Demo email processing agent",
        tier=AgentTier.PREMIUM,
        smtp_server="smtp.gmail.com",
        username="demo@example.com"
    )
    
    # Create agent instance
    agent = await agent_registry.create_agent("email", config)
    if not agent:
        print("Failed to create email agent")
        return
    
    print(f"Created agent: {agent.config.name}")
    
    # Test email operations
    email_tasks = [
        {
            "action": "send",
            "to": "recipient@example.com",
            "subject": "Test Email",
            "body": "This is a test email from AI Mega Agents Factory",
            "html": False
        },
        {
            "action": "read",
            "folder": "INBOX",
            "limit": 5,
            "unread_only": True
        },
        {
            "action": "classify",
            "content": "URGENT: Please review this important invoice that needs immediate payment. The deadline is tomorrow!"
        }
    ]
    
    for task in email_tasks:
        print(f"\nExecuting email {task['action']} operation...")
        result = await agent.execute(task)
        
        if result.success:
            print(f"Operation completed in {result.execution_time:.2f}s")
            print(f"Result: {result.data['result'][:200]}...")
        else:
            print(f"Operation failed: {result.error}")
    
    # Stop the agent
    await agent_registry.stop_agent(agent.config.agent_id)
    print("Email agent stopped")


async def demo_document_processing():
    """Demonstrate document processing agent"""
    print("\n=== Document Processing Agent Demo ===")
    
    # Create agent configuration
    config = DocumentConfig(
        name="Document Processor 1",
        description="Demo document processing agent",
        tier=AgentTier.BASIC,
        max_file_size_mb=5,
        ocr_enabled=True
    )
    
    # Create agent instance
    agent = await agent_registry.create_agent("document_processing", config)
    if not agent:
        print("Failed to create document processing agent")
        return
    
    print(f"Created agent: {agent.config.name}")
    
    # Sample document content
    sample_text = """
    AI Mega Agents Factory Documentation
    
    This document outlines the capabilities and usage of the AI Mega Agents Factory.
    The system provides 49 specialized AI agents for various business tasks.
    
    Key Features:
    - Plug-and-play architecture
    - Scalable microservices
    - Comprehensive API
    - Built-in monetization
    """
    
    # Test document operations
    document_tasks = [
        {
            "action": "extract",
            "data": sample_text,
            "file_type": "txt"
        },
        {
            "action": "analyze",
            "content": sample_text
        },
        {
            "action": "convert",
            "content": sample_text,
            "source_format": "txt",
            "target_format": "html"
        },
        {
            "action": "ocr",
            "image_data": "base64_encoded_image_data_here"
        }
    ]
    
    for task in document_tasks:
        print(f"\nExecuting document {task['action']} operation...")
        result = await agent.execute(task)
        
        if result.success:
            print(f"Operation completed in {result.execution_time:.2f}s")
            print(f"Result: {result.data['result'][:200]}...")
        else:
            print(f"Operation failed: {result.error}")
    
    # Stop the agent
    await agent_registry.stop_agent(agent.config.agent_id)
    print("Document processing agent stopped")


async def demo_multi_agent_workflow():
    """Demonstrate multi-agent workflow"""
    print("\n=== Multi-Agent Workflow Demo ===")
    
    # Create multiple agents
    agents = {}
    
    # Data analysis agent
    da_config = DataAnalysisConfig(
        name="Workflow Data Analyst",
        description="Data analysis for workflow",
        tier=AgentTier.PREMIUM
    )
    agents["data"] = await agent_registry.create_agent("data_analysis", da_config)
    
    # Document processing agent
    doc_config = DocumentConfig(
        name="Workflow Doc Processor",
        description="Document processing for workflow",
        tier=AgentTier.PREMIUM
    )
    agents["doc"] = await agent_registry.create_agent("document_processing", doc_config)
    
    # Email agent
    email_config = EmailConfig(
        name="Workflow Email Handler",
        description="Email handling for workflow",
        tier=AgentTier.PREMIUM
    )
    agents["email"] = await agent_registry.create_agent("email", email_config)
    
    print(f"Created {len(agents)} agents for workflow")
    
    # Simulate a business workflow
    # 1. Process a document to extract data
    doc_result = await agents["doc"].execute({
        "action": "extract",
        "data": "Product,Sales,Region\nWidget A,1000,North\nWidget B,1500,South",
        "file_type": "csv"
    })
    
    if doc_result.success:
        print("✓ Document processed successfully")
        
        # 2. Analyze the extracted data
        analysis_result = await agents["data"].execute({
            "data": "Product,Sales,Region\nWidget A,1000,North\nWidget B,1500,South",
            "analysis_type": "summary"
        })
        
        if analysis_result.success:
            print("✓ Data analysis completed")
            
            # 3. Send email report
            email_result = await agents["email"].execute({
                "action": "send",
                "to": "manager@company.com",
                "subject": "Weekly Sales Report",
                "body": f"Analysis complete. Results: {analysis_result.data['result'][:100]}...",
                "html": False
            })
            
            if email_result.success:
                print("✓ Email report sent")
            else:
                print("✗ Email sending failed")
        else:
            print("✗ Data analysis failed")
    else:
        print("✗ Document processing failed")
    
    # Clean up agents
    for agent_name, agent in agents.items():
        if agent:
            await agent_registry.stop_agent(agent.config.agent_id)
    
    print("Workflow completed and agents cleaned up")


async def demo_error_handling():
    """Demonstrate error handling and edge cases"""
    print("\n=== Error Handling Demo ===")
    
    # Create a free tier agent
    config = DataAnalysisConfig(
        name="Free Tier Agent",
        description="Demo free tier limitations",
        tier=AgentTier.FREE
    )
    
    agent = await agent_registry.create_agent("data_analysis", config)
    if not agent:
        print("Failed to create agent")
        return
    
    # Test tier limitations
    large_data = "x," * 5000  # Large data to exceed free tier
    result = await agent.execute({
        "data": large_data,
        "analysis_type": "summary"
    })
    
    if not result.success:
        print(f"✓ Tier limitation enforced: {result.error}")
    
    # Test invalid operations
    result = await agent.execute({
        "data": "test",
        "analysis_type": "invalid_type"
    })
    
    if not result.success:
        print(f"✓ Invalid operation handled: {result.error}")
    
    await agent_registry.stop_agent(agent.config.agent_id)


async def main():
    """Main demo function"""
    print("AI Mega Agents Factory - Sample Usage Demo")
    print("=" * 50)
    
    # Run all demos
    await demo_data_analysis()
    await demo_email_agent()
    await demo_document_processing()
    await demo_multi_agent_workflow()
    await demo_error_handling()
    
    # Show system status
    print("\n=== System Status ===")
    active_agents = agent_registry.list_agents()
    print(f"Active agents: {len(active_agents)}")
    
    available_types = agent_registry.list_agent_types()
    print(f"Available agent types: {', '.join(available_types)}")
    
    print("\nDemo completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())