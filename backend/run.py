"""
Start the FastAPI backend server
"""
import sys
import os
import uvicorn

if __name__ == "__main__":
    # Add current directory to path
    sys.path.insert(0, os.path.dirname(__file__))
    
    # Run uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
