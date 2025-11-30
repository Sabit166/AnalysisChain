"""
LLM Provider abstraction layer with caching support for Claude and Gemini
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import timedelta
import anthropic
import google.generativeai as genai
from groq import Groq
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential


class CacheType(Enum):
    """Types of caching mechanisms"""
    NONE = "none"
    PROMPT_CACHE = "prompt_cache"  # Claude
    CONTEXT_CACHE = "context_cache"  # Gemini


@dataclass
class Message:
    """Unified message format"""
    role: str  # 'user', 'assistant', 'system'
    content: str
    cache_control: Optional[Dict[str, Any]] = None


@dataclass
class LLMResponse:
    """Unified response format"""
    content: str
    usage: Dict[str, int]
    cache_info: Dict[str, Any]
    model: str


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, api_key: str, model: str, max_tokens: int):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
    
    @abstractmethod
    def generate(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        use_cache: bool = True
    ) -> LLMResponse:
        """Generate response from messages"""
        pass
    
    @abstractmethod
    def create_cached_context(
        self,
        context: str,
        cache_ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create cached context for reuse"""
        pass


class ClaudeProvider(BaseLLMProvider):
    """Claude API provider with prompt caching"""
    
    def __init__(self, api_key: str, model: str, max_tokens: int, cache_ttl: int = 300):
        super().__init__(api_key, model, max_tokens)
        self.client = anthropic.Anthropic(api_key=api_key)
        self.cache_ttl = cache_ttl
        logger.info(f"Initialized Claude provider with model: {model}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def generate(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        use_cache: bool = True
    ) -> LLMResponse:
        """
        Generate response with Claude API using prompt caching
        
        Claude prompt caching works by marking content blocks with cache_control.
        The API automatically caches these blocks for 5 minutes (default).
        """
        # Convert messages to Claude format
        claude_messages = []
        for msg in messages:
            message_dict = {
                "role": msg.role if msg.role != "system" else "user",
                "content": msg.content
            }
            
            # Add cache control if enabled and specified
            if use_cache and msg.cache_control:
                message_dict["cache_control"] = msg.cache_control
            
            claude_messages.append(message_dict)
        
        # Build request parameters
        request_params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": claude_messages,
            "temperature": temperature
        }
        
        # Add system prompt with caching if provided
        if system_prompt:
            if use_cache:
                # Mark system prompt for caching
                request_params["system"] = [
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"}
                    }
                ]
            else:
                request_params["system"] = system_prompt
        
        try:
            response = self.client.messages.create(**request_params)
            
            # Extract usage information
            usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "cache_creation_input_tokens": getattr(
                    response.usage, "cache_creation_input_tokens", 0
                ),
                "cache_read_input_tokens": getattr(
                    response.usage, "cache_read_input_tokens", 0
                )
            }
            
            # Calculate cache efficiency
            total_input = usage["input_tokens"] + usage["cache_read_input_tokens"]
            cache_hit_rate = (
                usage["cache_read_input_tokens"] / total_input * 100
                if total_input > 0 else 0
            )
            
            cache_info = {
                "cache_type": "prompt_cache",
                "cache_hit_rate": cache_hit_rate,
                "tokens_saved": usage["cache_read_input_tokens"]
            }
            
            logger.info(
                f"Claude response - Input: {usage['input_tokens']}, "
                f"Output: {usage['output_tokens']}, "
                f"Cache read: {usage['cache_read_input_tokens']}, "
                f"Cache hit rate: {cache_hit_rate:.1f}%"
            )
            
            return LLMResponse(
                content=response.content[0].text,
                usage=usage,
                cache_info=cache_info,
                model=self.model
            )
        
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise
    
    def create_cached_context(
        self,
        context: str,
        cache_ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a message with cache control for Claude
        
        Args:
            context: Context to cache
            cache_ttl: Not used for Claude (uses default 5 min)
            
        Returns:
            Message dict with cache control
        """
        return {
            "role": "user",
            "content": context,
            "cache_control": {"type": "ephemeral"}
        }


class GeminiProvider(BaseLLMProvider):
    """Gemini API provider with context caching"""
    
    def __init__(self, api_key: str, model: str, max_tokens: int, cache_ttl: int = 3600):
        super().__init__(api_key, model, max_tokens)
        genai.configure(api_key=api_key)
        self.cache_ttl = cache_ttl
        self._cached_contents = {}  # Track cached content
        logger.info(f"Initialized Gemini provider with model: {model}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def generate(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        use_cache: bool = True
    ) -> LLMResponse:
        """
        Generate response with Gemini API using context caching
        
        Gemini caching works by creating cached content objects that can be
        referenced in subsequent requests.
        """
        # Build conversation history
        history = []
        current_content = ""
        
        for msg in messages[:-1]:  # All but last message go to history
            if msg.role == "user":
                history.append({"role": "user", "parts": [msg.content]})
            elif msg.role == "assistant":
                history.append({"role": "model", "parts": [msg.content]})
        
        # Last message is the current prompt
        if messages:
            current_content = messages[-1].content
        
        try:
            # Create model configuration
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": self.max_tokens,
            }
            
            # Initialize model
            model = genai.GenerativeModel(
                model_name=self.model,
                generation_config=generation_config,
                system_instruction=system_prompt
            )
            
            # Start chat with history
            chat = model.start_chat(history=history)
            
            # Generate response
            response = chat.send_message(current_content)
            
            # Extract usage (Gemini provides limited usage info)
            usage = {
                "input_tokens": response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0,
                "output_tokens": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0,
                "total_tokens": response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0
            }
            
            cache_info = {
                "cache_type": "context_cache",
                "cache_enabled": use_cache,
                "history_length": len(history)
            }
            
            logger.info(
                f"Gemini response - Total tokens: {usage['total_tokens']}, "
                f"History length: {len(history)}"
            )
            
            return LLMResponse(
                content=response.text,
                usage=usage,
                cache_info=cache_info,
                model=self.model
            )
        
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    def create_cached_context(
        self,
        context: str,
        cache_ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create cached content for Gemini
        
        Args:
            context: Context to cache
            cache_ttl: Cache time-to-live in seconds
            
        Returns:
            Cached content reference
        """
        ttl = cache_ttl or self.cache_ttl
        
        try:
            # Create cached content
            cached_content = genai.caching.CachedContent.create(
                model=self.model,
                contents=[{"role": "user", "parts": [{"text": context}]}],
                ttl=timedelta(seconds=ttl)
            )
            
            cache_name = cached_content.name
            self._cached_contents[cache_name] = cached_content
            
            logger.info(f"Created Gemini cached content: {cache_name} (TTL: {ttl}s)")
            
            return {
                "cache_name": cache_name,
                "ttl": ttl,
                "size": len(context)
            }
        
        except Exception as e:
            logger.error(f"Failed to create Gemini cache: {e}")
            raise


class GroqProvider(BaseLLMProvider):
    """Groq API provider - Fast inference with open-source models"""
    
    def __init__(self, api_key: str, model: str, max_tokens: int, temperature: float = 0.7):
        super().__init__(api_key, model, max_tokens)
        self.client = Groq(api_key=api_key)
        self.temperature = temperature
        logger.info(f"Initialized Groq provider with model: {model}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def generate(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        use_cache: bool = True
    ) -> LLMResponse:
        """
        Generate response with Groq API
        
        Groq doesn't support explicit caching, but is extremely fast
        making repeated calls efficient.
        """
        # Convert messages to Groq format
        groq_messages = []
        
        # Add system prompt if provided
        if system_prompt:
            groq_messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Add conversation messages
        for msg in messages:
            groq_messages.append({
                "role": msg.role if msg.role != "system" else "user",
                "content": msg.content
            })
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=groq_messages,
                temperature=temperature,
                max_tokens=self.max_tokens
            )
            
            # Extract usage information
            usage = {
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0
            }
            
            cache_info = {
                "cache_type": "none",
                "cache_enabled": False,
                "note": "Groq uses fast inference instead of caching"
            }
            
            logger.info(
                f"Groq response - Input: {usage['input_tokens']}, "
                f"Output: {usage['output_tokens']}, "
                f"Total: {usage['total_tokens']}"
            )
            
            return LLMResponse(
                content=response.choices[0].message.content or "",
                usage=usage,
                cache_info=cache_info,
                model=self.model
            )
        
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise
    
    def create_cached_context(
        self,
        context: str,
        cache_ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Groq doesn't support caching, return basic context info
        
        Args:
            context: Context text
            cache_ttl: Not used for Groq
            
        Returns:
            Context info dict
        """
        return {
            "context": context,
            "cache_supported": False,
            "note": "Groq uses fast inference, no caching needed"
        }


class LLMProviderFactory:
    """Factory for creating LLM providers"""
    
    @staticmethod
    def create_provider(
        provider_type: str,
        api_key: str,
        model: str,
        max_tokens: int,
        cache_ttl: int = 300,
        temperature: float = 0.7
    ) -> BaseLLMProvider:
        """
        Create LLM provider instance
        
        Args:
            provider_type: 'claude', 'gemini', or 'groq'
            api_key: API key for the provider
            model: Model name
            max_tokens: Maximum output tokens
            cache_ttl: Cache time-to-live (not used for Groq)
            temperature: Temperature for generation (used for Groq)
            
        Returns:
            Provider instance
        """
        if provider_type.lower() == "claude":
            return ClaudeProvider(api_key, model, max_tokens, cache_ttl)
        elif provider_type.lower() == "gemini":
            return GeminiProvider(api_key, model, max_tokens, cache_ttl)
        elif provider_type.lower() == "groq":
            return GroqProvider(api_key, model, max_tokens, temperature)
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")
