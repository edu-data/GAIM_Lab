"""
GAIM Lab Backend Tests — conftest

프로젝트 루트를 sys.path에 추가하여 core.agents 등을 import 가능하게 합니다.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
