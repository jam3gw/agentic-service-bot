import os
import sys
from pathlib import Path

# Add the parent directory to PYTHONPATH so we can import from handlers, services, etc.
api_dir = Path(__file__).parent.parent
sys.path.append(str(api_dir)) 