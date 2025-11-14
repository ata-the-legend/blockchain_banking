#!/bin/bash

# Blockchain Banking API - Quick Setup Script
set -e

echo "==================================="
echo "Blockchain Banking API - Setup"
echo "==================================="
echo

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  IMPORTANT: Edit .env and add your FAUCET_PRIVATE_KEY before starting!"
    echo
    read -p "Press Enter after you've updated the .env file..."
fi

# Build and start services
echo "Building Docker images..."
docker-compose build

echo
echo "Starting services..."
docker-compose up -d

echo
echo "Waiting for services to be ready..."
sleep 10

echo
echo "Checking service status..."
docker-compose ps

echo
echo "==================================="
echo "✅ Setup Complete!"
echo "==================================="
echo
echo "API is running at: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo "API Alternative Docs: http://localhost:8000/redoc"
echo
echo "Useful commands:"
echo "  View logs:        docker-compose logs -f app"
echo "  Stop services:    docker-compose down"
echo "  Restart:          docker-compose restart"
echo "  Run migrations:   docker-compose exec app alembic upgrade head"
echo
echo "Test the API:"
echo '  curl -X POST "http://localhost:8000/create_account" -H "Content-Type: application/json" -d '"'"'{"name":"alice"}'"'"
echo
