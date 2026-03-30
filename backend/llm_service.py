"""
Integration example for Tongyi LLM with FastAPI
"""
from llm_wrapper import get_llm, TongyiLLMWrapper
import logging

logger = logging.getLogger(__name__)


async def integrate_llm_to_api():
    """
    Example: How to integrate LLM with FastAPI endpoints
    
    Usage in main.py:
    
    from llm_service import get_llm
    
    @app.post("/chat")
    async def chat(request: ChatRequest):
        llm = get_llm()
        response = llm.chat(request.message)
        return ChatResponse(response=response, conversation_id="...")
    """
    
    try:
        # Get LLM instance
        llm = get_llm()
        
        # Example 1: Simple chat
        print("Example 1: Simple Chat")
        response = llm.chat("你好，请自我介绍一下")
        print(f"Response: {response}\n")
        
        # Example 2: Continuous conversation
        print("Example 2: Continuous Conversation")
        response2 = llm.chat("你能帮我总结一下吗？")
        print(f"Response: {response2}\n")
        
        # Example 3: With system prompt
        print("Example 3: With System Prompt")
        llm.clear_history()
        response3 = llm.chat_with_system_prompt(
            user_message="写一个简单的Python函数",
            system_prompt="你是一个专业的Python编程助手"
        )
        print(f"Response: {response3}\n")
        
        # Example 4: Get conversation history
        print("Example 4: Conversation History")
        history = llm.get_history()
        print(f"History: {history}")
        
    except Exception as e:
        logger.error(f"Error in integration example: {str(e)}")
        raise


# To run this example:
# 1. Set DASHSCOPE_API_KEY in .env file
# 2. Run: python -m backend.llm_service
if __name__ == "__main__":
    import asyncio
    asyncio.run(integrate_llm_to_api())
