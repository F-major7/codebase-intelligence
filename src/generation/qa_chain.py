"""Q&A generation chain using Claude for intelligent code explanations."""

from anthropic import Anthropic
from typing import List, Dict, Optional
import os


class CodeQAChain:
    """Generates natural language answers to code questions using Claude.
    
    This class takes retrieved code chunks and uses Claude 3.5 Sonnet to generate
    intelligent, cited answers that help developers understand the codebase.
    
    Example:
        >>> qa = CodeQAChain()
        >>> answer = qa.ask(
        ...     question="How does the loader filter files?",
        ...     retrieved_chunks=[...]
        ... )
        >>> print(answer['answer'])
    """
    
    def __init__(self, model: str = "claude-haiku-4-5-20251001", temperature: float = 0.0):
        """Initialize the Q&A chain.
        
        Args:
            model: Claude model to use for generation
            temperature: Sampling temperature (0.0 = deterministic)
            
        Raises:
            ValueError: If ANTHROPIC_API_KEY environment variable is not set
        """
        # Check for Anthropic API key
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable not set. "
                "Please set it to use Claude for answer generation."
            )
        
        # Initialize Anthropic client
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Store configuration
        self.model = model
        self.temperature = temperature
        
        print(f"Initializing Q&A chain with model: {model}")
    
    def _format_context(self, chunks: List[Dict]) -> str:
        """Format retrieved code chunks into structured context.
        
        Creates a formatted string with file paths and code content that
        provides clear context for the LLM to generate answers.
        
        Args:
            chunks: List of chunk dicts with keys:
                   - content: Code text
                   - file_path: Source file path
                   - chunk_id: Position within file
                   
        Returns:
            Formatted context string with code blocks
            
        Example:
            >>> chunks = [{'content': 'def foo():', 'file_path': 'test.py', 'chunk_id': 0}]
            >>> context = qa._format_context(chunks)
            >>> 'File: test.py' in context
            True
        """
        if not chunks:
            return "No relevant code found in the codebase."
        
        formatted_sections = []
        
        for chunk in chunks:
            content = chunk.get('content', '')
            file_path = chunk.get('file_path', 'unknown')
            chunk_id = chunk.get('chunk_id', 0)
            
            # Create a section for each chunk
            section = f"""File: {file_path} (Part {chunk_id + 1})
```python
{content}
```
"""
            formatted_sections.append(section)
        
        return "\n".join(formatted_sections)
    
    def _build_prompt(self, question: str, context: str) -> str:
        """Build the complete prompt for Claude.
        
        Constructs a structured prompt that instructs Claude to answer
        based only on the provided code context, with citations.
        
        Args:
            question: User's question about the codebase
            context: Formatted code context from retrieved chunks
            
        Returns:
            Complete prompt string ready for Claude API
        """
        prompt = f"""You are an expert code documentation assistant helping developers understand a codebase.

CODE CONTEXT:
{context}

USER QUESTION:
{question}

INSTRUCTIONS:
1. Answer the question based ONLY on the provided code context
2. Include specific file paths and function/class names when referencing code
3. Use code examples from the context when helpful
4. Be concise but complete - aim for clarity
5. If the code context doesn't contain enough information to answer, 
   say "The provided code doesn't contain information about this."
6. Structure your answer with clear sections if answering multiple points

Format your answer to be helpful for a developer reading it.

ANSWER:"""
        
        return prompt
    
    def ask(self, question: str, retrieved_chunks: List[Dict]) -> Dict:
        """Generate an answer to a question using retrieved code chunks.
        
        Main method that orchestrates the answer generation process:
        1. Formats the code context
        2. Builds the prompt
        3. Calls Claude API
        4. Returns structured result with answer and metadata
        
        Args:
            question: User's question about the codebase
            retrieved_chunks: List of relevant code chunks from vector search
            
        Returns:
            Dictionary with keys:
            - answer: Generated answer text
            - sources: List of source file paths
            - num_chunks_used: Number of chunks provided as context
            - model: Model used for generation
            
        Raises:
            Exception: If API call fails (with informative error message)
            
        Example:
            >>> qa = CodeQAChain()
            >>> chunks = [{'content': '...', 'file_path': 'src/main.py', 'chunk_id': 0}]
            >>> result = qa.ask("How does this work?", chunks)
            >>> print(result['answer'])
            The code in src/main.py shows...
        """
        try:
            # Format context from chunks
            context = self._format_context(retrieved_chunks)
            
            # Build complete prompt
            prompt = self._build_prompt(question, context)
            
            # Call Anthropic API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract answer text
            answer_text = response.content[0].text
            
            # Extract unique source file paths
            sources = [chunk['file_path'] for chunk in retrieved_chunks]
            
            print(f"🧠 Generated answer using {len(retrieved_chunks)} code chunks")
            
            return {
                'answer': answer_text,
                'sources': sources,
                'num_chunks_used': len(retrieved_chunks),
                'model': self.model
            }
            
        except Exception as e:
            error_msg = f"Failed to generate answer: {str(e)}"
            print(f"❌ {error_msg}")
            
            # Return error in structured format
            return {
                'answer': f"Error generating answer: {str(e)}",
                'sources': [],
                'num_chunks_used': 0,
                'model': self.model
            }

