import sys
import os

try:
    from app.search import data_sources
    print("SUCCESS: imported data_sources")
    print("CONTENTS:", dir(data_sources))
except Exception as e:
    import traceback
    traceback.print_exc()
