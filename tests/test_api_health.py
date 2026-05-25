from fastapi.testclient import TestClient
import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to path so we can import api
sys.path.append(os.path.join(os.getcwd(), "src"))

# Mock db_pool before importing app
with patch("psycopg2.pool.SimpleConnectionPool") as mock_pool:
    from dashboard.api import app

client = TestClient(app)

def test_health_check_healthy():
    with patch("dashboard.api.db_pool") as mock_db_pool:
        mock_db_pool.getconn.return_value = MagicMock()
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "database": "up"}
        mock_db_pool.getconn.assert_called_once()
        mock_db_pool.putconn.assert_called_once()

def test_health_check_unhealthy_no_pool():
    with patch("dashboard.api.db_pool", None):
        response = client.get("/health")
        assert response.status_code == 503
        assert response.json()["detail"] == {"status": "unhealthy", "database": "down"}

def test_health_check_unhealthy_db_fail():
    with patch("dashboard.api.db_pool") as mock_db_pool:
        mock_db_pool.getconn.side_effect = Exception("DB Fail")
        response = client.get("/health")
        assert response.status_code == 503
        assert response.json()["detail"] == {"status": "unhealthy", "database": "down"}
