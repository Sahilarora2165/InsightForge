#!/bin/bash
# InternalKnowledgeHub - Development Setup Script
# This script sets up the development environment

set -e

echo "🚀 Setting up InternalKnowledgeHub development environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ $1 is not installed. Please install it first.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ $1 is installed${NC}"
}

echo ""
echo "Checking prerequisites..."
check_command python3
check_command pip3
check_command node
check_command npm
check_command docker
check_command docker-compose

# Create Python virtual environment
echo ""
echo "Setting up Python virtual environment..."
if [ ! -d "backend/.venv" ]; then
    python3 -m venv backend/.venv
    echo -e "${GREEN}✓ Created virtual environment${NC}"
else
    echo -e "${YELLOW}! Virtual environment already exists${NC}"
fi

# Activate virtual environment and install dependencies
echo ""
echo "Installing Python dependencies..."
source backend/.venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
echo -e "${GREEN}✓ Python dependencies installed${NC}"

# Install frontend dependencies
echo ""
echo "Installing Node.js dependencies..."
cd frontend
npm install
cd ..
echo -e "${GREEN}✓ Node.js dependencies installed${NC}"

# Create environment files
echo ""
echo "Setting up environment files..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env from template${NC}"
else
    echo -e "${YELLOW}! .env already exists${NC}"
fi

if [ ! -f "frontend/.env" ]; then
    cp frontend/.env.example frontend/.env
    echo -e "${GREEN}✓ Created frontend/.env from template${NC}"
else
    echo -e "${YELLOW}! frontend/.env already exists${NC}"
fi

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p backend/uploads
mkdir -p backend/chroma_data
mkdir -p backend/logs
echo -e "${GREEN}✓ Directories created${NC}"

# Initialize database
echo ""
echo "Do you want to start Docker services (PostgreSQL, Redis, Ollama)? (y/n)"
read -r start_docker

if [ "$start_docker" = "y" ]; then
    echo "Starting Docker services..."
    docker-compose up -d postgres redis ollama
    echo -e "${GREEN}✓ Docker services started${NC}"
    
    # Wait for services to be ready
    echo "Waiting for services to be ready..."
    sleep 10
    
    # Pull Ollama model
    echo ""
    echo "Do you want to pull the Ollama llama3 model? This may take a while. (y/n)"
    read -r pull_ollama
    
    if [ "$pull_ollama" = "y" ]; then
        echo "Pulling llama3 model..."
        docker exec -it ollama ollama pull llama3
        echo "Pulling nomic-embed-text model..."
        docker exec -it ollama ollama pull nomic-embed-text
        echo -e "${GREEN}✓ Ollama models pulled${NC}"
    fi
fi

# Run database migrations
echo ""
echo "Running database migrations..."
cd backend
source .venv/bin/activate
alembic upgrade head 2>/dev/null || echo -e "${YELLOW}! Alembic migrations not yet configured${NC}"
cd ..

# Final message
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Setup complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "To start development:"
echo ""
echo "  1. Start all services with Docker:"
echo "     docker-compose up -d"
echo ""
echo "  2. Or start services individually:"
echo "     - Backend: cd backend && source .venv/bin/activate && flask run"
echo "     - Frontend: cd frontend && npm run dev"
echo "     - Worker: cd backend && celery -A worker.tasks worker -l info"
echo ""
echo "  3. Access the application:"
echo "     - Frontend: http://localhost:5173"
echo "     - Backend API: http://localhost:8000"
echo "     - API Docs: http://localhost:8000/api/docs"
echo ""
echo "For more information, see README.md"
