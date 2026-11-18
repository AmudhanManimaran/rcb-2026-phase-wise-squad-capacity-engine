import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database import ping  # noqa: E402

DB_AVAILABLE = ping()
requires_db = pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL database not reachable (run the data loader first)")


@pytest.fixture(scope="session")
def season():
    if not DB_AVAILABLE:
        pytest.skip("database not available")
    from backend.engine.season_data import SeasonData
    return SeasonData.load()
