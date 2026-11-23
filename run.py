"""
Root launcher for Voice AI Doctor Appointment Assistant.
Runs FastAPI backend serving both REST API, WebSocket Voice Pipeline,
and built React Dashboard on http://localhost:8000
"""

import os
import sys
import uvicorn
from loguru import logger

def main():
    logger.info("Starting Apex Health Voice AI Assistant Server...")
    logger.info("Open http://localhost:8000 in your browser to test the full app.")
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    main()
