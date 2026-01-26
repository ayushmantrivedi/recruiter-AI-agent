
import sys
import os

# Add project root to sys.path
# This allows scripts in scripts/SubDir/ to import 'app'
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
