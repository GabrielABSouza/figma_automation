# Figma Automation Pipeline — Command Runner

default:
    @just --list

# Backend
dev:
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 9000

test:
    pytest backend/tests/ -v

lint:
    ruff check backend/

format:
    ruff format backend/

check: lint test

# Schema
schema:
    python -m backend.schemas.generate
    @echo "✓ ui-schema.json generated at /schemas/"

# Figma Plugin
plugin-install:
    cd figma-plugin && npm install

plugin-build:
    cd figma-plugin && npm run build

plugin-dev:
    cd figma-plugin && npm run dev

# Setup
install:
    pip install -e ".[dev]"

install-all:
    pip install -e ".[dev,db]"

# Database
db-migrate:
    alembic upgrade head
