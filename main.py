"""
Startup script for the Metrics Tracker web application.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.web.app import app, config

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Starting Metrics Tracker")
    print("=" * 60)
    print(f"Server: http://{config.web.host}:{config.web.port}")
    print(f"Database: {config.database.path}")
    print(f"Debug mode: {config.web.debug}")
    print("=" * 60)
    print("\nPress Ctrl+C to stop\n")
    
    app.run(
        host=config.web.host,
        port=config.web.port,
        debug=config.web.debug
    )
