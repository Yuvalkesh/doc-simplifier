import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

# Vercel serverless config - increase timeout to 60s (requires Pro plan for >10s)
# Hobby plan is limited to 10s, so this enables max available time
config = {
    "maxDuration": 60
}

# Vercel serverless handler
