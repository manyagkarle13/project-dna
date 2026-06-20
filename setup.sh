#!/bin/bash

# Project DNA Setup Script
# This script handles complete backend and frontend setup

echo "🧬 Project DNA - Complete Setup Script"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "Backend/manage.py" ]; then
    echo "❌ Error: Please run this script from the Project-DNA root directory"
    exit 1
fi

echo -e "${BLUE}Step 1: Setting up Backend${NC}"
cd Backend

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate venv (for Windows and Unix)
if [ -f "venv/Scripts/activate" ]; then
    # Windows
    . venv/Scripts/activate
else
    # Unix
    source venv/bin/activate
fi

echo "Installing backend dependencies..."
pip install -r requirements.txt -q

echo "Running database migrations..."
python manage.py migrate --noinput -q

echo -e "${GREEN}✓ Backend setup complete${NC}"
echo ""

cd ..

echo -e "${BLUE}Step 2: Setting up Frontend${NC}"
cd Frontend

echo "Installing frontend dependencies..."
npm install --silent

echo "Building frontend..."
npm run build

echo -e "${GREEN}✓ Frontend setup complete${NC}"
echo ""

cd ..

echo -e "${GREEN}======================================"
echo "✨ Setup Complete!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo ""
echo "1. Backend (Django):"
echo "   cd Backend"
echo "   source venv/bin/activate  # Unix"
echo "   # OR on Windows:"
echo "   venv\\Scripts\\activate"
echo "   python manage.py runserver"
echo ""
echo "2. Frontend (Vite dev server - optional):"
echo "   cd Frontend"
echo "   npm run dev"
echo ""
echo "3. Access the application:"
echo "   http://localhost:8000  (Backend + compiled frontend)"
echo "   http://localhost:5173  (Frontend dev server, if running)"
echo ""
echo "📝 For detailed configuration, see DEPLOYMENT.md"
echo ""
