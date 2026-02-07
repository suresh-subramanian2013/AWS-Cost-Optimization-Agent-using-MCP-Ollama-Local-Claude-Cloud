"""
Example usage of the AWS Cost Monitoring System.
Demonstrates various queries and report generation capabilities.
"""
import logging
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from agent_orchestrator import AgentOrchestrator
from aws_cost_service import AWSCostService
from config import Config

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

console = Console()


def print_response(title: str, response: str):
    """Print formatted response."""
    console.print(Panel(
        Markdown(response),
        title=title,
        border_style="green"
    ))


def example_basic_cost_query():
    """Example: Basic cost query for last 30 days."""
    console.print("\n[bold cyan]Example 1: Basic Cost Query[/bold cyan]\n")
    
    agent = AgentOrchestrator()
    try:
        query = "What were my total AWS costs for the last 30 days?"
        console.print(f"[yellow]Query:[/yellow] {query}\n")
        
        response = agent.process_query(query)
        print_response("Cost Summary", response)
    finally:
        agent.close()


def example_service_breakdown():
    """Example: Service-level cost breakdown."""
    console.print("\n[bold cyan]Example 2: Service Cost Breakdown[/bold cyan]\n")
    
    agent = AgentOrchestrator()
    try:
        query = "Break down my AWS costs by service for the last month. Which services cost the most?"
        console.print(f"[yellow]Query:[/yellow] {query}\n")
        
        response = agent.process_query(query)
        print_response("Service Breakdown", response)
    finally:
        agent.close()


def example_cost_forecast():
    """Example: Cost forecast for next month."""
    console.print("\n[bold cyan]Example 3: Cost Forecast[/bold cyan]\n")
    
    agent = AgentOrchestrator()
    try:
        query = "What is my forecasted AWS cost for the next 30 days?"
        console.print(f"[yellow]Query:[/yellow] {query}\n")
        
        response = agent.process_query(query)
        print_response("Cost Forecast", response)
    finally:
        agent.close()


def example_anomaly_detection():
    """Example: Detect cost anomalies."""
    console.print("\n[bold cyan]Example 4: Cost Anomaly Detection[/bold cyan]\n")
    
    agent = AgentOrchestrator()
    try:
        query = "Are there any unusual spending patterns or cost anomalies in the last 30 days?"
        console.print(f"[yellow]Query:[/yellow] {query}\n")
        
        response = agent.process_query(query)
        print_response("Anomaly Detection", response)
    finally:
        agent.close()


def example_optimization_recommendations():
    """Example: Get optimization recommendations."""
    console.print("\n[bold cyan]Example 5: Optimization Recommendations[/bold cyan]\n")
    
    agent = AgentOrchestrator()
    try:
        query = "What are the top cost optimization recommendations for my AWS account?"
        console.print(f"[yellow]Query:[/yellow] {query}\n")
        
        response = agent.process_query(query)
        print_response("Optimization Recommendations", response)
    finally:
        agent.close()


def example_comprehensive_report():
    """Example: Generate comprehensive cost report."""
    console.print("\n[bold cyan]Example 6: Comprehensive Cost Report[/bold cyan]\n")
    
    agent = AgentOrchestrator()
    try:
        query = (
            "Generate a comprehensive AWS cost report for the last 30 days including: "
            "1) Total costs, 2) Cost breakdown by service, 3) Any anomalies detected, "
            "4) Cost forecast for next month, and 5) Top optimization recommendations."
        )
        console.print(f"[yellow]Query:[/yellow] {query}\n")
        
        response = agent.process_query(query)
        print_response("Comprehensive Report", response)
    finally:
        agent.close()


def example_different_llm_backends():
    """Example: Using different LLM backends."""
    console.print("\n[bold cyan]Example 7: Different LLM Backends[/bold cyan]\n")
    
    query = "What were my AWS costs yesterday?"
    
    # Try OpenAI
    if Config.OPENAI_API_KEY:
        console.print("[yellow]Using OpenAI GPT...[/yellow]")
        agent = AgentOrchestrator(llm_provider='openai')
        try:
            response = agent.process_query(query)
            print_response("OpenAI Response", response)
        finally:
            agent.close()
    
    # Try Anthropic
    if Config.ANTHROPIC_API_KEY:
        console.print("\n[yellow]Using Anthropic Claude...[/yellow]")
        agent = AgentOrchestrator(llm_provider='anthropic')
        try:
            response = agent.process_query(query)
            print_response("Anthropic Response", response)
        finally:
            agent.close()
    
    # Try Ollama (local)
    console.print("\n[yellow]Using Ollama (local)...[/yellow]")
    try:
        agent = AgentOrchestrator(llm_provider='ollama')
        try:
            response = agent.process_query(query)
            print_response("Ollama Response", response)
        finally:
            agent.close()
    except Exception as e:
        console.print(f"[red]Ollama not available: {e}[/red]")


def main():
    """Run all examples."""
    console.print(Panel(
        "[bold green]AWS Cost Monitoring System - Example Usage[/bold green]\n"
        "Demonstrating various cost analysis queries and LLM backends",
        border_style="blue"
    ))
    
    try:
        # Run examples
        example_basic_cost_query()
        example_service_breakdown()
        example_cost_forecast()
        example_anomaly_detection()
        example_optimization_recommendations()
        example_comprehensive_report()
        example_different_llm_backends()
        
        console.print("\n[bold green]✓ All examples completed![/bold green]\n")
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Examples interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error running examples: {e}[/red]")
        raise


if __name__ == '__main__':
    main()
