import sys
from unittest.mock import MagicMock

# Mock chromadb if not installed
try:
    import chromadb  # noqa: F401
except ImportError:
    mock_chromadb = MagicMock()
    sys.modules["chromadb"] = mock_chromadb
