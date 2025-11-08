#!/bin/bash

# Script to recreate Python virtual environment
# Usage: bash setup_env.sh

echo "🔧 Setting up Python virtual environment..."

# Remove existing venv if it exists
if [ -d "venv" ]; then
    echo "📦 Removing existing virtual environment..."
    rm -rf venv
fi

# Create new virtual environment
echo "🆕 Creating new virtual environment 'venv'..."
python3 -m venv venv

# Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your BLACKBOX_API_KEY"
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To deactivate, run:"
echo "  deactivate"
echo ""
echo "Don't forget to set your BLACKBOX_API_KEY in the .env file!"
