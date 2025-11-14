# Blockchain Banking API

A production-ready FastAPI application for blockchain-based banking simulation using PostgreSQL and Web3.py.

## Features

- **Async Architecture**: Fully async FastAPI with async SQLAlchemy and asyncpg
- **Blockchain Integration**: EVM-compatible chain interaction with web3.py
- **Database**: PostgreSQL with Alembic migrations
- **Best Practices**: MVC pattern, dependency injection, structured logging, error handling
- **Docker**: Complete Docker Compose setup for easy deployment

## Tech Stack

- **FastAPI** - Modern async web framework
- **SQLAlchemy 2.0** - Async ORM with asyncpg driver
- **PostgreSQL 16** - Relational database
- **Web3.py** - Ethereum interaction library
- **Alembic** - Database migrations
- **Structlog** - Structured logging
- **Docker & Docker Compose** - Containerization

## Project Structure

```
app/
├── __init__.py
├── main.py              # FastAPI app entry point
├── settings.py          # Environment configuration
├── database.py          # Async DB session management
├── models/              # SQLAlchemy models
│   └── user.py
├── schemas/             # Pydantic schemas
│   └── user.py
├── repositories/        # Business logic layer
│   └── account.py
├── routers/             # API endpoints
│   └── api.py
└── utils/               # Utilities
    └── web3_client.py

migrations/              # Alembic migrations
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- (Optional) Python 3.12+ for local development

### 1. Clone and Configure

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your FAUCET_PRIVATE_KEY
nano .env
```

### 2. Run with Docker

```bash
# Build and start all services
docker-compose up --build

# The API will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### 3. Run Migrations (automatic on startup, but manual command if needed)

```bash
docker-compose exec app alembic upgrade head
```

## API Endpoints

### Create Account
```bash
POST /create_account
Body: {"name": "alice"}
Response: {"name": "alice", "address": "0x...", "private_key": "0x..."}
```

### Get Balance
```bash
GET /get_balance?name=alice&token_address=0x7a816c115b8aed1fee7029dd490613f20063b9c3
Response: {"balance": 1000000000000000000}
```

### Transfer Tokens
```bash
POST /transfer
Body: {
  "from_name": "alice",
  "to_name": "bob",
  "amount": 100000000000000000,
  "token_address": "0x7a816c115b8aed1fee7029dd490613f20063b9c3"
}
Response: {"success": true, "tx_hash": "0x..."}
```

### Get Initial Fund (Faucet)
```bash
POST /get_initial_fund
Body: {"name": "alice"}
Response: {"success": true, "tx_hash": "0x..."}
```

## Local Development

### Setup

```bash
# Install dependencies (if using Poetry)
poetry install

# Or with pip
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Start PostgreSQL (Docker)
docker-compose up db -d

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Create Migration

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app --cov-report=html
```

## Security Notes

⚠️ **IMPORTANT**: This is a simulation application with intentional security trade-offs:

- Private keys are stored encrypted at rest using a symmetric key loaded from the environment, but
  the protection is only as strong as your key management
- No authentication/authorization implemented
- Suitable for development/testing only
- **DO NOT use in production with real funds**

For production:
- Use hardware security modules (HSM) or key management services
- Implement proper authentication (JWT, OAuth2)
- Encrypt sensitive data at rest
- Use secure key derivation and storage
- Add rate limiting and API security measures

## Architecture

### MVC Pattern

- **Models** (`models/`): SQLAlchemy ORM models for database schemas
- **Repositories** (`repositories/`): Business logic and service layer
- **Routers** (`routers/`): API endpoints and request handling

### Async Flow

1. FastAPI receives request → async route handler
2. Repository function called → async DB query with SQLAlchemy
3. Web3 operations → async RPC calls
4. Response returned → fully non-blocking

### Error Handling

- Custom exceptions for business logic errors
- HTTPException for API errors
- Structured logging for debugging
- Graceful degradation on RPC failures

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `RPC_URL` | EVM-compatible RPC endpoint | Required |
| `FAUCET_PRIVATE_KEY` | Master account private key | Required |
| `PRIVATE_KEY_ENCRYPTION_KEY` | Base64 Fernet key for encrypting user private keys | Required |
| `APP_HOST` | API host | `0.0.0.0` |
| `APP_PORT` | API port | `8000` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `CHAIN_ID` | Blockchain chain ID | `1000` |
| `GAS_LIMIT` | Default gas limit | `100000` |

Generate a compliant Fernet key with:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## License

MIT
