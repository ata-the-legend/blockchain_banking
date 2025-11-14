"""Test suite for blockchain banking API."""

import pytest
from httpx import AsyncClient

from app.main import app
from app.utils.web3_client import web3_client


@pytest.fixture(autouse=True)
def mock_send_native_token(monkeypatch):
    """Mock Web3 native token transfer to avoid network calls."""

    async def _mock_send_native_token(*args, **kwargs):
        return "0xtestfaucettxhash"

    monkeypatch.setattr(
        web3_client,
        "send_native_token",
        _mock_send_native_token,
        raising=True,
    )

    return _mock_send_native_token


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint returns health status."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_create_account():
    """Test account creation endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/create_account", json={"name": "test_user"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test_user"
        assert "address" in data
        assert "private_key" in data
        assert data["address"].startswith("0x")
        assert data["faucet_tx_hash"] == "0xtestfaucettxhash"


@pytest.mark.asyncio
async def test_create_duplicate_account():
    """Test that creating duplicate account fails."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create first account
        await client.post(
            "/api/create_account", json={"name": "duplicate_user"}
        )

        # Try to create duplicate
        response = await client.post(
            "/api/create_account", json={"name": "duplicate_user"}
        )
        assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_balance_nonexistent_account():
    """Test getting balance for nonexistent account."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/get_balance",
            params={
                "name": "nonexistent",
                "token": "USDC",
            },
        )
        assert response.status_code == 404
