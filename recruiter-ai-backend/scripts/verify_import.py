
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from app.routes import recruiter
    print("SUCCESS: Imported recruiter")
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
