"""
Main entry point for AnalysisChain CLI
"""

from .cli import cli
from .logging_config import setup_logging

if __name__ == '__main__':
    setup_logging()
    cli()
