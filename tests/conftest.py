
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent / "src"
tests_path = Path(__file__).parent

print(f"sys.path: {sys.path}")
print(f"src_path: {src_path}")
print(f"tests_path: {tests_path}")

if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

if str(tests_path) not in sys.path:
    sys.path.insert(0, str(tests_path))
