
import os
import sys

# Ensure backend root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.config.settings import settings
import logging

# We want to see what repository.py sees, but repository.py logic is manual env var reading if DATABASE_URL not set.
# Let's import repository logic to be sure.
# But repository.py connects on import? No.
# We will just inspect settings first.

print("=== Settings Dump ===")
print(f"HOST: {settings.timescale_host}")
print(f"PORT: {settings.timescale_port}")
print(f"USER: {settings.timescale_user}")
# Mask password partially
pwd = settings.timescale_password
masked = pwd[0] + "***" + pwd[-1] if len(pwd) > 2 else "***"
print(f"PASS: {masked} (Len: {len(pwd)})")
print(f"DB: {settings.timescale_db}")
print("=====================")

# Check if env vars differ
print("ENV TIMESCALE_HOST:", os.getenv("TIMESCALE_HOST"))
