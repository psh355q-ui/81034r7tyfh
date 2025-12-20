"""
Simple script to start the backend server
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=5000,
        reload=True,
        log_level="info"
    )
