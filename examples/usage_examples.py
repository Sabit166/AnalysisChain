"""
Example usage scripts for AnalysisChain Agent
"""

from pathlib import Path
from src.agent import AnalysisChainAgent


def example_1_basic_usage():
    """Basic usage: Load documents and ask questions"""
    print("\n" + "="*80)
    print("Example 1: Basic Usage")
    print("="*80)
    
    # Initialize agent
    agent = AnalysisChainAgent(provider="claude")
    print(f"✓ Created session: {agent.session_id}")
    
    # Load instruction
    instruction = agent.load_instruction_file(
        Path("examples/instruction_research.txt")
    )
    print("✓ Loaded instruction file")
    
    # Load documents
    summary = agent.load_source_documents(
        document_paths=[Path("your_document.pdf")],
        add_to_vector_db=True
    )
    print(f"✓ Loaded {summary['documents_loaded']} document(s)")
    
    # Ask question
    response, metadata = agent.process_query(
        query="What are the main findings?",
        instruction=instruction,
        use_rag=True,
        use_cache=True
    )
    
    print("\nResponse:", response[:200] + "...")
    print(f"\nToken usage: {metadata['usage']}")


def example_2_multi_step():
    """Multi-step analysis with different instruction sets"""
    print("\n" + "="*80)
    print("Example 2: Multi-Step Analysis")
    print("="*80)
    
    agent = AnalysisChainAgent(provider="claude")
    print(f"✓ Session: {agent.session_id}")
    
    # Load documents
    agent.load_source_documents(
        document_paths=[Path("document.pdf")],
        add_to_vector_db=True
    )
    
    # Stage 1: Initial analysis
    instruction1 = agent.load_instruction_file(
        Path("examples/instruction_research.txt")
    )
    
    queries_stage1 = [
        "Summarize the introduction",
        "What is the research question?",
        "Describe the methodology"
    ]
    
    print("\nStage 1: Basic Analysis")
    for query in queries_stage1:
        response, metadata = agent.process_query(
            query=query,
            instruction=instruction1,
            use_rag=True,
            use_cache=True
        )
        print(f"  Query: {query}")
        print(f"  Tokens: {metadata['usage']['input_tokens']}")
        print(f"  Cache hit: {metadata['cache_info'].get('cache_hit_rate', 0):.1f}%")
    
    # Stage 2: Deep dive with new instructions
    instruction2 = agent.load_instruction_file(
        Path("examples/instruction_code_doc.txt")
    )
    
    queries_stage2 = [
        "Analyze the code samples",
        "Document the algorithms used"
    ]
    
    print("\nStage 2: Technical Analysis")
    for query in queries_stage2:
        response, metadata = agent.process_query(
            query=query,
            instruction=instruction2,
            use_rag=True,
            use_cache=True
        )
        print(f"  Query: {query}")
        print(f"  Tokens: {metadata['usage']['input_tokens']}")


def example_3_batch_processing():
    """Batch processing with output generation"""
    print("\n" + "="*80)
    print("Example 3: Batch Processing")
    print("="*80)
    
    agent = AnalysisChainAgent(provider="gemini")
    print(f"✓ Session: {agent.session_id}")
    
    # Load documents
    agent.load_source_documents(
        document_paths=[Path("document.pdf")],
        add_to_vector_db=True
    )
    
    instruction = agent.load_instruction_file(
        Path("examples/instruction_research.txt")
    )
    
    # Batch queries
    queries = [
        "What are the key contributions?",
        "Explain the experimental setup",
        "What are the main results?",
        "What are the limitations?",
        "What future work is suggested?"
    ]
    
    # Process all queries
    results = agent.multi_step_operation(
        queries=queries,
        instruction=instruction,
        save_outputs=True,
        output_dir=Path("./outputs/batch_example")
    )
    
    print(f"\n✓ Processed {len(results)} queries")
    print(f"✓ Outputs saved to: ./outputs/batch_example")
    
    # Show summary
    total_tokens = sum(r['metadata']['usage'].get('input_tokens', 0) for r in results)
    print(f"\nTotal input tokens: {total_tokens}")


def example_4_rag_comparison():
    """Compare results with and without RAG"""
    print("\n" + "="*80)
    print("Example 4: RAG Comparison")
    print("="*80)
    
    agent = AnalysisChainAgent(provider="claude")
    
    # Load documents
    agent.load_source_documents(
        document_paths=[Path("document.pdf")],
        add_to_vector_db=True
    )
    
    query = "What machine learning techniques are discussed?"
    
    # Without RAG (full context)
    print("\nWithout RAG:")
    response1, meta1 = agent.process_query(
        query=query,
        use_rag=False,
        use_cache=True
    )
    print(f"  Tokens: {meta1['usage']['input_tokens']}")
    
    # With RAG (selective context)
    print("\nWith RAG:")
    response2, meta2 = agent.process_query(
        query=query,
        use_rag=True,
        rag_chunks=5,
        use_cache=True
    )
    print(f"  Tokens: {meta2['usage']['input_tokens']}")
    print(f"  Chunks retrieved: {meta2['rag_chunks_retrieved']}")
    
    token_savings = meta1['usage']['input_tokens'] - meta2['usage']['input_tokens']
    savings_pct = (token_savings / meta1['usage']['input_tokens']) * 100
    print(f"\nToken savings: {token_savings} ({savings_pct:.1f}%)")


def example_5_session_resume():
    """Resume a previous session"""
    print("\n" + "="*80)
    print("Example 5: Session Resume")
    print("="*80)
    
    # Create initial session
    agent1 = AnalysisChainAgent(provider="claude")
    session_id = agent1.session_id
    
    print(f"✓ Created session: {session_id}")
    
    # Load documents
    agent1.load_source_documents(
        document_paths=[Path("document.pdf")],
        add_to_vector_db=True
    )
    
    # First query
    response1, _ = agent1.process_query(
        query="What is this document about?",
        use_rag=True,
        use_cache=True
    )
    
    print("✓ Processed first query")
    
    # Simulate closing and reopening
    del agent1
    
    # Resume session
    agent2 = AnalysisChainAgent(session_id=session_id)
    print(f"✓ Resumed session: {session_id}")
    
    # Get session summary
    summary = agent2.get_session_summary()
    print(f"\nSession info:")
    print(f"  Messages: {summary['message_count']}")
    print(f"  Documents: {summary['source_documents']}")
    print(f"  Vector DB chunks: {summary['vector_db_chunks']}")
    
    # Continue with follow-up
    response2, _ = agent2.process_query(
        query="Can you elaborate on that?",
        use_rag=True,
        use_cache=True
    )
    
    print("✓ Processed follow-up query with cached context")


if __name__ == "__main__":
    print("\nAnalysisChain Agent - Example Usage Scripts")
    print("=" * 80)
    print("\nNote: Update file paths with your actual documents before running!")
    print("\nAvailable examples:")
    print("  1. example_1_basic_usage()")
    print("  2. example_2_multi_step()")
    print("  3. example_3_batch_processing()")
    print("  4. example_4_rag_comparison()")
    print("  5. example_5_session_resume()")
    
    # Uncomment to run examples:
    # example_1_basic_usage()
    # example_2_multi_step()
    # example_3_batch_processing()
    # example_4_rag_comparison()
    # example_5_session_resume()
