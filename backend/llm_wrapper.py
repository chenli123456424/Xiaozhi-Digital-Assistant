"""
Tongyi LLM Wrapper using LangChain
"""
from typing import Optional, List, Generator
from langchain_community.llms import Tongyi
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
import logging

from config import settings

logger = logging.getLogger(__name__)


class TongyiLLMWrapper:
    """Wrapper for Tongyi LLM integration using LangChain"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "qwen-max",
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: Optional[int] = None,
    ):
        """
        Initialize Tongyi LLM Wrapper
        
        Args:
            api_key: Dashscope API Key (defaults to DASHSCOPE_API_KEY env var)
            model: Model name (default: qwen-max)
            temperature: Temperature for creativity (0-1)
            top_p: Top-p sampling parameter
            max_tokens: Maximum tokens to generate
        """
        self.api_key = api_key or settings.dashscope_api_key
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY is not configured")
        
        # Initialize Tongyi LLM
        self.llm = Tongyi(
            model=self.model,
            dashscope_api_key=self.api_key,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
        )
        
        # Message history for conversation context
        self.messages: List[BaseMessage] = []
        
        logger.info(f"Tongyi LLM initialized with model: {self.model}")
    
    def chat(self, user_message: str) -> str:
        """
        Send a message and get response
        
        Args:
            user_message: User input message
            
        Returns:
            Response from Tongyi LLM
        """
        try:
            # Add user message to history
            self.messages.append(HumanMessage(content=user_message))
            
            # Get response from LLM
            response = self.llm.invoke(self.messages)
            
            # Add AI response to history
            self.messages.append(AIMessage(content=response))
            
            logger.info(f"Generated response: {response[:100]}...")
            return response
            
        except Exception as e:
            logger.error(f"Error calling Tongyi LLM: {str(e)}")
            raise
    
    def chat_with_system_prompt(
        self,
        user_message: str,
        system_prompt: str = None
    ) -> str:
        """
        Send a message with system prompt
        
        Args:
            user_message: User input message
            system_prompt: System prompt for context
            
        Returns:
            Response from Tongyi LLM
        """
        try:
            # Build message list with system prompt
            messages = self.messages.copy()
            
            if system_prompt:
                messages.insert(0, HumanMessage(content=f"System: {system_prompt}"))
            
            messages.append(HumanMessage(content=user_message))
            
            # Get response
            response = self.llm.invoke(messages)
            
            # Add to conversation history
            self.messages.append(HumanMessage(content=user_message))
            self.messages.append(AIMessage(content=response))
            
            return response
            
        except Exception as e:
            logger.error(f"Error in chat_with_system_prompt: {str(e)}")
            raise
    
    def clear_history(self):
        """Clear conversation history"""
        self.messages = []
        logger.info("Conversation history cleared")
    
    def get_history(self) -> List[dict]:
        """
        Get formatted conversation history
        
        Returns:
            List of formatted messages
        """
        result = []
        for msg in self.messages:
            if isinstance(msg, HumanMessage):
                result.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                result.append({"role": "assistant", "content": msg.content})
        return result
    
    def set_model(self, model: str):
        """Change the model"""
        self.model = model
        self.llm = Tongyi(
            model=model,
            dashscope_api_key=self.api_key,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
        )
        logger.info(f"Model changed to: {model}")
    
    def chat_stream(self, user_message: str) -> Generator[str, None, None]:
        """
        Send a message and get streaming response
        
        Args:
            user_message: User input message
            
        Yields:
            Chunks of response text
        """
        try:
            # Add user message to history
            self.messages.append(HumanMessage(content=user_message))
            
            # Create LLM with streaming enabled
            streaming_llm = Tongyi(
                model=self.model,
                dashscope_api_key=self.api_key,
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens,
                streaming=True,  # Enable streaming
            )
            
            full_response = ""
            
            # Stream the response
            for chunk in streaming_llm.stream(self.messages):
                if chunk:
                    full_response += chunk
                    yield chunk
                    logger.debug(f"Streamed chunk: {chunk}")
            
            # Add complete AI response to history
            self.messages.append(AIMessage(content=full_response))
            logger.info(f"Streaming completed. Total response length: {len(full_response)}")
            
        except Exception as e:
            logger.error(f"Error in streaming chat: {str(e)}")
            error_msg = f"错误: {str(e)}"
            yield error_msg
            raise
    
    def chat_stream_with_system_prompt(
        self, 
        user_message: str, 
        system_prompt: str = None
    ) -> Generator[str, None, None]:
        """
        Send a message with system prompt and get streaming response
        
        Args:
            user_message: User input message
            system_prompt: System prompt for context
            
        Yields:
            Chunks of response text
        """
        try:
            # Build message list with system prompt
            messages = self.messages.copy()
            
            if system_prompt:
                messages.insert(0, HumanMessage(content=f"System: {system_prompt}"))
            
            messages.append(HumanMessage(content=user_message))
            
            # Create LLM with streaming enabled
            streaming_llm = Tongyi(
                model=self.model,
                dashscope_api_key=self.api_key,
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens,
                streaming=True,  # Enable streaming
            )
            
            full_response = ""
            
            # Stream the response
            for chunk in streaming_llm.stream(messages):
                if chunk:
                    full_response += chunk
                    yield chunk
            
            # Add to conversation history
            self.messages.append(HumanMessage(content=user_message))
            self.messages.append(AIMessage(content=full_response))
            
        except Exception as e:
            logger.error(f"Error in streaming chat with system prompt: {str(e)}")
            error_msg = f"错误: {str(e)}"
            yield error_msg
            raise


# Global LLM instance
_llm_instance: Optional[TongyiLLMWrapper] = None


def get_llm() -> TongyiLLMWrapper:
    """Get or create global LLM instance"""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = TongyiLLMWrapper(
            api_key=settings.dashscope_api_key,
            model=settings.model_name,
            temperature=settings.temperature,
            top_p=settings.top_p,
            max_tokens=settings.max_tokens,
        )
    return _llm_instance


def initialize_llm(
    api_key: Optional[str] = None,
    model: str = "qwen-max",
    **kwargs
) -> TongyiLLMWrapper:
    """Initialize LLM with custom settings"""
    global _llm_instance
    _llm_instance = TongyiLLMWrapper(
        api_key=api_key,
        model=model,
        **kwargs
    )
    return _llm_instance
