"""
Test script to verify LLM initialization
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from config import settings
from llm_wrapper import TongyiLLMWrapper

if __name__ == "__main__":
    print("=" * 60)
    print("Testing LLM Initialization")
    print("=" * 60)
    
    print(f"\n1. Checking configuration:")
    print(f"   DASHSCOPE_API_KEY is set: {bool(settings.dashscope_api_key)}")
    print(f"   Model: {settings.model_name}")
    print(f"   Temperature: {settings.temperature}")
    
    print(f"\n2. Attempting to initialize LLM...")
    try:
        llm = TongyiLLMWrapper(
            api_key=settings.dashscope_api_key,
            model=settings.model_name,
        )
        print("   ✅ LLM initialized successfully!")
        
        print(f"\n3. Attempting to make a test call...")
        response = llm.chat("你好，请问你是谁？")
        print(f"   ✅ Response received!")
        print(f"   Response: {response[:100]}...")
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)
