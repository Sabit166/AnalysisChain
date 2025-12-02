"""
Command-line interface for AnalysisChain Agent
"""

import sys
from pathlib import Path
from typing import Optional, List
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from loguru import logger

from .agent import AnalysisChainAgent
from .config import settings


console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    AnalysisChain - AI Agent with Intelligent Caching and Context Management
    
    Efficiently process large documents with follow-up operations while minimizing token costs.
    """
    pass


@cli.command()
@click.option(
    '--provider',
    type=click.Choice(['claude', 'gemini', 'groq'], case_sensitive=False),
    default=None,
    help='LLM provider (defaults to config)'
)
@click.option(
    '--model',
    type=str,
    default=None,
    help='Model name (defaults to config)'
)
def new_session(provider: Optional[str], model: Optional[str]):
    """Create a new session"""
    try:
        agent = AnalysisChainAgent(provider=provider, model=model)
        
        console.print(Panel(
            f"[bold green]New session created![/bold green]\n\n"
            f"Session ID: [cyan]{agent.session_id}[/cyan]\n"
            f"Provider: [yellow]{agent.provider_type}[/yellow]\n"
            f"Model: [yellow]{agent.model}[/yellow]",
            title="Session Created"
        ))
        
        console.print(f"\n💡 Use this session ID for follow-up operations: [cyan]{agent.session_id}[/cyan]")
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.argument('session_id', type=str)
@click.argument('document_paths', nargs=-1, required=True, type=click.Path(exists=True))
@click.option(
    '--no-vector-db',
    is_flag=True,
    help='Skip adding to vector database'
)
def load_documents(session_id: str, document_paths: tuple, no_vector_db: bool):
    """Load source documents into a session"""
    try:
        agent = AnalysisChainAgent(session_id=session_id)
        
        console.print(f"[bold]Loading {len(document_paths)} document(s)...[/bold]")
        
        summary = agent.load_source_documents(
            document_paths=[Path(p) for p in document_paths],
            add_to_vectordb=not no_vector_db
        )
        
        console.print(Panel(
            f"[bold green]Documents loaded successfully![/bold green]\n\n"
            f"New documents: [cyan]{summary['new_documents']}[/cyan]\n"
            f"Skipped (already loaded): [cyan]{summary['skipped_documents']}[/cyan]\n"
            f"Total chunks: [cyan]{summary['total_chunks']}[/cyan]\n"
            f"Vector DB: [cyan]{'Enabled' if not no_vector_db else 'Disabled'}[/cyan]",
            title="Load Complete"
        ))
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.argument('session_id', type=str)
@click.argument('query', type=str)
@click.option(
    '--instruction',
    type=click.Path(exists=True),
    help='Instruction file path'
)
@click.option(
    '--no-rag',
    is_flag=True,
    help='Disable RAG context retrieval'
)
@click.option(
    '--no-cache',
    is_flag=True,
    help='Disable caching'
)
@click.option(
    '--chunks',
    type=int,
    default=5,
    help='Number of RAG chunks to retrieve'
)
@click.option(
    '--temperature',
    type=float,
    default=0.7,
    help='LLM temperature (0.0 - 1.0)'
)
@click.option(
    '--output',
    type=click.Path(),
    help='Save response to file'
)
def query(
    session_id: str,
    query: str,
    instruction: Optional[str],
    no_rag: bool,
    no_cache: bool,
    chunks: int,
    temperature: float,
    output: Optional[str]
):
    """Process a query in a session"""
    try:
        agent = AnalysisChainAgent(session_id=session_id)
        
        # Load instruction if provided
        instruction_text = None
        if instruction:
            instruction_text = agent.load_instruction_file(Path(instruction))
            console.print(f"[dim]Loaded instruction file: {instruction}[/dim]\n")
        
        console.print("[bold]Processing query...[/bold]")
        
        response, metadata = agent.process_query(
            query=query,
            instruction=instruction_text,
            use_rag=not no_rag,
            rag_chunks=chunks,
            use_cache=not no_cache,
            temperature=temperature
        )
        
        # Display response
        console.print("\n" + "="*80 + "\n")
        console.print(Markdown(response))
        console.print("\n" + "="*80 + "\n")
        
        # Display metadata
        usage = metadata['usage']
        console.print(f"\n[dim]Token Usage:[/dim]")
        console.print(f"  Input: {usage.get('input_tokens', 0)}")
        console.print(f"  Output: {usage.get('output_tokens', 0)}")
        
        if 'cache_read_input_tokens' in usage:
            console.print(f"  Cache Read: {usage['cache_read_input_tokens']}")
            console.print(f"  Cache Hit Rate: {metadata['cache_info']['cache_hit_rate']:.1f}%")
        
        # Save output if requested
        if output:
            output_path = agent.generate_output_file(response, Path(output))
            console.print(f"\n💾 Saved to: [cyan]{output_path}[/cyan]")
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.argument('session_id', type=str)
@click.argument('queries_file', type=click.Path(exists=True))
@click.option(
    '--instruction',
    type=click.Path(exists=True),
    help='Instruction file path'
)
@click.option(
    '--output-dir',
    type=click.Path(),
    help='Directory for saving outputs'
)
def batch_query(
    session_id: str,
    queries_file: str,
    instruction: Optional[str],
    output_dir: Optional[str]
):
    """Process multiple queries from a file"""
    try:
        agent = AnalysisChainAgent(session_id=session_id)
        
        # Load instruction if provided
        instruction_text = None
        if instruction:
            instruction_text = agent.load_instruction_file(Path(instruction))
            console.print(f"[dim]Loaded instruction file: {instruction}[/dim]\n")
        
        # Load queries
        with open(queries_file, 'r', encoding='utf-8') as f:
            queries = [line.strip() for line in f if line.strip()]
        
        console.print(f"[bold]Processing {len(queries)} queries...[/bold]\n")
        
        # Process queries
        results = agent.multi_step_operation(
            queries=queries,
            instruction=instruction_text,
            save_outputs=True,
            output_dir=Path(output_dir) if output_dir else None
        )
        
        # Display summary
        console.print(f"\n[bold green]Batch processing complete![/bold green]\n")
        
        for i, result in enumerate(results, 1):
            console.print(f"Query {i}: {result['query'][:60]}...")
            console.print(f"  Tokens: {result['metadata']['usage'].get('total_tokens', 'N/A')}")
            if result['output_path']:
                console.print(f"  Output: {result['output_path']}")
            console.print()
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.argument('session_id', type=str, required=False)
def info(session_id: Optional[str]):
    """Show session information"""
    try:
        if session_id:
            # Show specific session
            agent = AnalysisChainAgent(session_id=session_id)
            summary = agent.get_session_summary()
            
            console.print(Panel(
                f"[bold]Session ID:[/bold] [cyan]{summary['session_id']}[/cyan]\n"
                f"[bold]Provider:[/bold] {summary['provider']}\n"
                f"[bold]Model:[/bold] {summary['model']}\n"
                f"[bold]Created:[/bold] {summary['created_at']}\n"
                f"[bold]Last Accessed:[/bold] {summary['last_accessed']}\n\n"
                f"[bold]Statistics:[/bold]\n"
                f"  Source Documents: {summary['source_documents']}\n"
                f"  Generated Outputs: {summary['generated_outputs']}\n"
                f"  Messages: {summary['message_count']}\n"
                f"  Vector DB Chunks: {summary['vector_db_chunks']}",
                title="Session Information"
            ))
        else:
            # List all sessions
            from .session_manager import SessionManager
            manager = SessionManager(settings.session_storage_path)
            sessions = manager.list_sessions()
            
            if not sessions:
                console.print("[yellow]No sessions found[/yellow]")
                return
            
            table = Table(title="All Sessions")
            table.add_column("Session ID", style="cyan")
            table.add_column("Provider", style="yellow")
            table.add_column("Model", style="yellow")
            table.add_column("Messages", style="green")
            table.add_column("Last Accessed", style="dim")
            
            for session in sessions:
                table.add_row(
                    session['session_id'][:8] + "...",
                    session['provider'],
                    session['model'],
                    str(session['message_count']),
                    session['last_accessed'][:19]
                )
            
            console.print(table)
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.argument('session_id', type=str)
@click.confirmation_option(prompt='Are you sure you want to delete this session?')
def delete_session(session_id: str):
    """Delete a session"""
    try:
        from .session_manager import SessionManager
        manager = SessionManager(settings.session_storage_path)
        
        if manager.delete_session(session_id):
            console.print(f"[bold green]Session {session_id} deleted successfully[/bold green]")
        else:
            console.print(f"[bold red]Session {session_id} not found[/bold red]")
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
def cleanup():
    """Clean up expired sessions"""
    try:
        from .session_manager import SessionManager
        manager = SessionManager(settings.session_storage_path)
        
        deleted = manager.cleanup_expired_sessions()
        console.print(f"[bold green]Cleaned up {deleted} expired session(s)[/bold green]")
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
def clear_vectordb(confirm: bool):
    """Clear the vector database (removes all document embeddings)"""
    try:
        import shutil
        from .config import settings
        
        vectordb_path = Path(settings.vector_db_path)
        
        if not vectordb_path.exists():
            console.print("[yellow]Vector database is already empty[/yellow]")
            return
        
        # Confirmation
        if not confirm:
            console.print(f"\n[bold red]⚠️  WARNING[/bold red]")
            console.print(f"This will delete all document embeddings in: [cyan]{vectordb_path}[/cyan]")
            console.print("\nThis action cannot be undone!\n")
            
            if not click.confirm("Are you sure you want to continue?"):
                console.print("[yellow]Operation cancelled[/yellow]")
                return
        
        # Delete vector database
        shutil.rmtree(vectordb_path)
        console.print(f"\n[green]✓[/green] Vector database cleared successfully")
        console.print(f"[dim]Deleted: {vectordb_path}[/dim]\n")
        
        logger.info("Vector database cleared")
        
    except Exception as e:
        logger.error(f"Failed to clear vector database: {e}")
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@cli.command()
@click.option('--all', 'clear_all', is_flag=True, help='Clear all sessions')
@click.option('--session-id', help='Clear specific session')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
def clear_sessions(clear_all: bool, session_id: Optional[str], confirm: bool):
    """Clear session data"""
    try:
        from .session_manager import SessionManager
        from .config import settings
        
        session_manager = SessionManager(storage_path=Path(settings.session_storage_path))
        
        # Validate options
        if not clear_all and not session_id:
            console.print("[red]Error:[/red] Must specify --all or --session-id")
            raise click.Abort()
        
        if clear_all and session_id:
            console.print("[red]Error:[/red] Cannot use both --all and --session-id")
            raise click.Abort()
        
        # Clear specific session
        if session_id:
            session = session_manager.get_session(session_id)
            if not session:
                console.print(f"[red]Error:[/red] Session not found: {session_id}")
                raise click.Abort()
            
            # Confirmation
            if not confirm:
                console.print(f"\n[bold yellow]⚠️  WARNING[/bold yellow]")
                console.print(f"This will delete session: [cyan]{session_id}[/cyan]")
                console.print(f"Created: {session.created_at}")
                console.print(f"Messages: {len(session.message_history)}")
                console.print("\nThis action cannot be undone!\n")
                
                if not click.confirm("Are you sure you want to continue?"):
                    console.print("[yellow]Operation cancelled[/yellow]")
                    return
            
            # Delete session
            session_manager.delete_session(session_id)
            console.print(f"\n[green]✓[/green] Session deleted: {session_id}\n")
            logger.info(f"Deleted session: {session_id}")
        
        # Clear all sessions
        elif clear_all:
            sessions = session_manager.list_sessions()
            
            if not sessions:
                console.print("[yellow]No sessions to clear[/yellow]")
                return
            
            # Confirmation
            if not confirm:
                console.print(f"\n[bold red]⚠️  WARNING[/bold red]")
                console.print(f"This will delete [red]ALL {len(sessions)} sessions[/red]")
                console.print("\nThis action cannot be undone!\n")
                
                if not click.confirm("Are you sure you want to continue?"):
                    console.print("[yellow]Operation cancelled[/yellow]")
                    return
            
            # Delete all sessions
            deleted = 0
            for session_info in sessions:
                if session_manager.delete_session(session_info['session_id']):
                    deleted += 1
            
            console.print(f"\n[green]✓[/green] Deleted {deleted} session(s)\n")
            logger.info(f"Deleted all sessions: {deleted}")
    
    except Exception as e:
        logger.error(f"Failed to clear sessions: {e}")
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@cli.command()
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
def clear_all(confirm: bool):
    """Clear everything (vector database + all sessions)"""
    try:
        import shutil
        from .session_manager import SessionManager
        from .config import settings
        
        vectordb_path = Path(settings.vector_db_path)
        session_manager = SessionManager(storage_path=Path(settings.session_storage_path))
        sessions = session_manager.list_sessions()
        
        # Confirmation
        if not confirm:
            console.print(f"\n[bold red]🚨 DANGER ZONE 🚨[/bold red]")
            console.print("\nThis will delete:")
            console.print(f"  • Vector database: [cyan]{vectordb_path}[/cyan]")
            console.print(f"  • All {len(sessions)} sessions")
            console.print(f"  • All conversation history")
            console.print(f"  • All metadata")
            console.print("\n[bold red]This action cannot be undone![/bold red]\n")
            
            if not click.confirm("Are you ABSOLUTELY sure?"):
                console.print("[yellow]Operation cancelled[/yellow]")
                return
        
        # Clear vector database
        if vectordb_path.exists():
            shutil.rmtree(vectordb_path)
            console.print("[green]✓[/green] Vector database cleared")
        
        # Clear all sessions
        deleted = 0
        for session_info in sessions:
            if session_manager.delete_session(session_info['session_id']):
                deleted += 1
        
        console.print(f"[green]✓[/green] Deleted {deleted} session(s)")
        console.print(f"\n[bold green]All data cleared successfully![/bold green]\n")
        
        logger.info("Cleared all data (vector database + sessions)")
        
    except Exception as e:
        logger.error(f"Failed to clear all data: {e}")
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


if __name__ == '__main__':
    cli()
