#!/usr/bin/env python3
"""
Recruiter AI CLI Client

A command-line interface for the Recruiter AI Platform.
Provides easy access to recruiter query processing and status checking.

Usage:
    recruiter health
    recruiter query "Find Python engineers in San Francisco" --recruiter 1
    recruiter status <query_id>
    recruiter results <query_id>
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

import requests
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.columns import Columns
import toml

# CLI app
app = typer.Typer(
    name="recruiter",
    help="Recruiter AI Platform CLI",
    add_completion=False,
)
console = Console()


class Config:
    """Configuration manager for the CLI client."""

    def __init__(self):
        self.config_file = Path.home() / ".recruiter" / "config.toml"
        self._config = self._load_config()

    def _get_config_file(self) -> Path:
        """Get the config file path (for testing)."""
        return self.config_file

    def _load_config(self) -> dict:
        """Load configuration from file."""
        if not self.config_file.exists():
            return {"backend_url": "http://localhost:8000"}

        try:
            with open(self.config_file, "r") as f:
                return toml.load(f)
        except Exception as e:
            console.print(f"[red]Error loading config file: {e}[/red]")
            return {"backend_url": "http://localhost:8000"}

    def get(self, key: str, default=None):
        """Get configuration value."""
        return self._config.get(key, default)

    def set(self, key: str, value):
        """Set configuration value."""
        self._config[key] = value
        self._save_config()

    def _save_config(self):
        """Save configuration to file."""
        self.config_file.parent.mkdir(exist_ok=True)
        with open(self.config_file, "w") as f:
            toml.dump(self._config, f)


cli_config = Config()


class APIClient:
    """API client for Recruiter AI Platform."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.timeout = 30

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling and retries."""
        url = f"{self.base_url}{endpoint}"
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise e
                console.print(f"[yellow]Request failed, retrying... ({attempt + 1}/{max_retries})[/yellow]")
                time.sleep(retry_delay)
                retry_delay *= 2

    def health_check(self) -> dict:
        """Check backend health."""
        response = self._make_request("GET", "/health")
        return response.json()

    def submit_query(self, query: str, recruiter_id: Optional[str] = None) -> dict:
        """Submit a recruiter query."""
        data = {"query": query}
        if recruiter_id:
            data["recruiter_id"] = recruiter_id

        response = self._make_request("POST", "/api/recruiter/query", json=data)
        return response.json()

    def get_query_status(self, query_id: str) -> dict:
        """Get query status and results."""
        response = self._make_request("GET", f"/api/recruiter/query/{query_id}")
        return response.json()


def get_client() -> APIClient:
    """Get configured API client."""
    backend_url = cli_config.get("backend_url", "http://localhost:8000")
    return APIClient(backend_url)


@app.command()
def health():
    """Check backend health status."""
    try:
        client = get_client()
        with console.status("[bold green]Checking backend health...") as status:
            result = client.health_check()

        # Display health status
        status_color = "green" if result.get("status") == "ok" else "red"
        console.print(f"[{status_color}]Backend Status: {result.get('status', 'unknown')}[/{status_color}]")

        # Display components
        table = Table(title="Component Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="magenta")

        db_status = result.get("db", "unknown")
        redis_status = result.get("redis", "unknown")

        table.add_row("Database", db_status)
        table.add_row("Redis Cache", redis_status)

        console.print(table)

        # Display timestamp
        if "timestamp" in result:
            console.print(f"[dim]Last checked: {result['timestamp']}[/dim]")

    except Exception as e:
        console.print(f"[red]Error checking health: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def query(
    query_text: str = typer.Argument(..., help="The recruiter search query"),
    recruiter: Optional[str] = typer.Option(None, "--recruiter", "-r", help="Recruiter ID"),
    wait: bool = typer.Option(False, "--wait", "-w", help="Wait for query completion"),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON"),
):
    """Submit a recruiter query and optionally wait for results."""
    try:
        client = get_client()

        # Submit query
        with console.status("[bold green]Submitting query...") as status:
            result = client.submit_query(query_text, recruiter)

        query_id = result.get("query_id")
        status_text = result.get("status", "unknown")

        if not query_id:
            console.print("[red]Error: No query ID returned[/red]")
            raise typer.Exit(1)

        console.print(f"[green]Query submitted successfully![/green]")
        console.print(f"Query ID: [bold cyan]{query_id}[/bold cyan]")
        console.print(f"Status: [bold]{status_text}[/bold]")

        if json_output:
            console.print_json(data=result)
            return

        if wait:
            # Wait for completion
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Processing query...", total=None)

                while True:
                    try:
                        status_result = client.get_query_status(query_id)
                        current_status = status_result.get("status", "unknown")

                        if current_status == "completed":
                            progress.update(task, description="[green]Query completed!")
                            break
                        elif current_status == "failed":
                            progress.update(task, description="[red]Query failed!")
                            break
                        elif current_status == "processing":
                            progress.update(task, description="Processing query...")

                        time.sleep(2)  # Poll every 2 seconds

                    except KeyboardInterrupt:
                        console.print("\n[yellow]Stopped waiting for results[/yellow]")
                        return
                    except Exception as e:
                        console.print(f"\n[red]Error checking status: {e}[/red]")
                        return

            # Display final results
            _display_query_results(status_result)

        else:
            console.print(f"\n[dim]Use 'recruiter status {query_id}' to check progress[/dim]")
            console.print(f"[dim]Use 'recruiter results {query_id}' to get final results[/dim]")

    except Exception as e:
        console.print(f"[red]Error submitting query: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def status(query_id: str = typer.Argument(..., help="Query ID to check")):
    """Check the status of a query."""
    try:
        client = get_client()
        result = client.get_query_status(query_id)

        status_text = result.get("status", "unknown")
        status_color = {
            "pending": "yellow",
            "processing": "blue",
            "completed": "green",
            "failed": "red"
        }.get(status_text, "white")

        console.print(f"Query ID: [bold cyan]{query_id}[/bold cyan]")
        console.print(f"Status: [{status_color}]{status_text}[/{status_color}]")

        if "processing_time" in result and result["processing_time"]:
            console.print(".2f")

        if status_text == "completed":
            total_leads = result.get("total_leads_found", 0)
            console.print(f"Total leads found: [green]{total_leads}[/green]")

        if "error" in result and result["error"]:
            console.print(f"[red]Error: {result['error']}[/red]")

    except Exception as e:
        console.print(f"[red]Error checking status: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def results(
    query_id: str = typer.Argument(..., help="Query ID to get results for"),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON"),
):
    """Get the results of a completed query."""
    try:
        client = get_client()
        result = client.get_query_status(query_id)

        if json_output:
            console.print_json(data=result)
            return

        _display_query_results(result)

    except Exception as e:
        console.print(f"[red]Error getting results: {e}[/red]")
        raise typer.Exit(1)


def _display_query_results(result: dict):
    """Display query results in a formatted way."""
    status = result.get("status", "unknown")

    if status != "completed":
        console.print(f"[yellow]Query status: {status}[/yellow]")
        if "error" in result and result["error"]:
            console.print(f"[red]Error: {result['error']}[/red]")
        return

    # Query info
    console.print(Panel.fit(
        f"[bold]Query:[/bold] {result.get('original_query', 'N/A')}\n"
        f"[bold]Status:[/bold] [green]{status}[/green]\n"
        ".2f"
        f"[bold]Total Leads:[/bold] {result.get('total_leads_found', 0)}"
    ))

    leads = result.get("leads", [])
    if not leads:
        console.print("[yellow]No leads found.[/yellow]")
        return

    # Leads table
    table = Table(title="Company Leads")
    table.add_column("Company", style="cyan", no_wrap=True)
    table.add_column("Score", style="green", justify="right")
    table.add_column("Confidence", style="blue", justify="right")
    table.add_column("Evidence Count", style="magenta", justify="right")
    table.add_column("Reasons", style="yellow")

    for lead in leads:
        reasons_text = "\n".join(lead.get("reasons", [])[:2])  # Show first 2 reasons
        if len(lead.get("reasons", [])) > 2:
            reasons_text += f"\n... and {len(lead.get('reasons', [])) - 2} more"

        table.add_row(
            lead.get("company", "N/A"),
            f"{lead.get('score', 0):.2f}",
            f"{lead.get('confidence', 0):.2f}",
            str(lead.get("evidence_count", 0)),
            reasons_text
        )

    console.print(table)


@app.command()
def config_cmd(
    key: str = typer.Argument(..., help="Configuration key"),
    value: Optional[str] = typer.Argument(None, help="Configuration value"),
):
    """Get or set configuration values."""
    if value is None:
        # Get configuration
        current_value = cli_config.get(key)
        if current_value is not None:
            console.print(f"{key}: {current_value}")
        else:
            console.print(f"[yellow]Configuration key '{key}' not found[/yellow]")
    else:
        # Set configuration
        cli_config.set(key, value)
        console.print(f"[green]Set {key} = {value}[/green]")


@app.callback()
def main(
    backend_url: Optional[str] = typer.Option(
        None,
        "--backend-url",
        help="Backend API URL (overrides config file)"
    ),
):
    """Recruiter AI Platform CLI"""
    if backend_url:
        cli_config.set("backend_url", backend_url)


if __name__ == "__main__":
    app()