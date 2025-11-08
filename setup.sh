#!/bin/bash
# Setup script for CyberIntel Summarizer

echo "Setting up CyberIntel Summarizer..."

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create logs directory
echo "Creating logs directory..."
mkdir -p logs

# Copy environment template
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env and add your NVD_API_KEY if you have one"
fi

echo ""
echo "Setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To initialize the database, run:"
echo "  python -m scripts.init_db"
echo ""
echo "To fetch CVEs, run:"
echo "  python -m scripts.fetch_nvd --days 7"
