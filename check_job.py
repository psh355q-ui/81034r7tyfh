import sys
sys.path.insert(0, 'd:/code/ai-trading-system')

import httpx

# Check backfill job status
job_id = "d965d077-2628-4d89-b57f-213f23d3bf52"

try:
    response = httpx.get(
        f"http://localhost:8001/api/backfill/status/{job_id}",
        timeout=10.0
    )
    
    if response.status_code == 200:
        job = response.json()
        print("백필 작업 상태:")
        print(f"  Status: {job['status']}")
        print(f"  Progress: {job['progress']}")
        print(f"  Created: {job['created_at']}")
        print(f"  Started: {job.get('started_at', 'N/A')}")
        print(f"  Completed: {job.get('completed_at', 'N/A')}")
        if job.get('error_message'):
            print(f"  Error: {job['error_message']}")
    else:
        print(f"Failed: HTTP {response.status_code}")
        
except Exception as e:
    print(f"Error: {e}")
