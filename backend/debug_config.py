"""
Debug script to check if configuration is loaded correctly
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

# Check environment variable directly
print("=" * 60)
print("1. Checking environment variables...")
print("=" * 60)
print(f"DASHSCOPE_API_KEY from os.environ: {os.environ.get('DASHSCOPE_API_KEY', 'NOT FOUND')}")

# Check .env file
print("\n" + "=" * 60)
print("2. Checking .env file...")
print("=" * 60)
env_file = os.path.join(os.path.dirname(__file__), '.env')
print(f"Looking for .env at: {env_file}")
print(f".env exists: {os.path.exists(env_file)}")

if os.path.exists(env_file):
    with open(env_file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if 'DASHSCOPE' in line:
                print(f"Found: {line.strip()}")

# Check if python-dotenv loads it
print("\n" + "=" * 60)
print("3. Testing python-dotenv...")
print("=" * 60)
try:
    from dotenv import load_dotenv
    loaded = load_dotenv(env_file)
    print(f"dotenv.load_dotenv() returned: {loaded}")
    print(f"DASHSCOPE_API_KEY after load_dotenv: {os.environ.get('DASHSCOPE_API_KEY', 'NOT FOUND')}")
except Exception as e:
    print(f"Error loading dotenv: {e}")

# Check config.py
print("\n" + "=" * 60)
print("4. Checking config.py...")
print("=" * 60)
try:
    from config import settings
    print(f"settings.dashscope_api_key: {settings.dashscope_api_key}")
    print(f"Is it set: {bool(settings.dashscope_api_key)}")
except Exception as e:
    print(f"Error importing settings: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Summary:")
print("=" * 60)
if os.environ.get('DASHSCOPE_API_KEY'):
    print("✅ Environment variable is set correctly")
else:
    print("❌ Environment variable NOT set - you need to run: python run.py")
    print("   (not: python.exe run.py or venv\\Scripts\\python.exe run.py)")
