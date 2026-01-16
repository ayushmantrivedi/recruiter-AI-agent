import pytest
import sys

# Run pytest and capture output to a file with explicit encoding
with open("pytest_output.txt", "w", encoding="utf-8") as f:
    class Tee:
        def write(self, string):
            f.write(string)
            sys.__stdout__.write(string)
        def flush(self):
            f.flush()
            sys.__stdout__.flush()
            
    # Capture stdout/stderr isn"t easy with pytest.main direct invocation usually
    # But we can just use subprocess
    import subprocess
    import subprocess
    # Capture args
    cmd_args = sys.argv[1:] if len(sys.argv) > 1 else ["tests/"]
    result = subprocess.run(
        [sys.executable, "-m", "pytest", *cmd_args, "-v"],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    f.write(result.stdout)
    f.write(result.stderr)
    print("Done running tests")
