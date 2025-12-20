"""Test dotenv loading"""
import os
from pathlib import Path

# Find .env file
project_root = Path(__file__).parent
env_file = project_root / ".env"

print(f"Script location: {Path(__file__)}")
print(f"Project root: {project_root}")
print(f".env file path: {env_file}")
print(f".env file exists: {env_file.exists()}")
print()

# Load .env
from dotenv import load_dotenv
load_dotenv(env_file, override=True, verbose=True)

# Check values
print("\nEnvironment variables after loading:")
print(f"  TIMESCALE_HOST: {os.getenv('TIMESCALE_HOST')}")
print(f"  TIMESCALE_PORT: {os.getenv('TIMESCALE_PORT')}")
print(f"  TIMESCALE_USER: {os.getenv('TIMESCALE_USER')}")
print(f"  TIMESCALE_DATABASE: {os.getenv('TIMESCALE_DATABASE')}")
