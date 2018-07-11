import pytest
from pathlib import Path

pytest.main([Path(__file__).parents[0] / "tests"])
