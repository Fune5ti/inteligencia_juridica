import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
# Add the project root (parent of the 'src' package) so that 'import src.*' works.
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
