
import sys
import os

sys.path.insert(0, os.getcwd())

print("Attempting to import app.utils.logger...")
try:
    import app.utils.logger
    print("SUCCESS: app.utils.logger imported")
    print("Content:", dir(app.utils.logger))
except ImportError as e:
    print(f"FAIL: app.utils.logger failed: {e}")

print("\nAttempting to import app.main...")
try:
    from app import main
    print("SUCCESS: app.main imported")
except Exception as e:
    print(f"FAIL: app.main failed: {e}")
    import traceback
    traceback.print_exc()
