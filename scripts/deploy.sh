#!/bin/bash

# 🚀 Azalea Air Deployment Script
# This script automates the setup and deployment process

set -e  # Exit on any error

echo "🚀 Starting Azalea Air deployment..."

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python first."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
else
    echo "📦 Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "📥 Installing requirements..."
pip install -r requirements.txt

# Initialize database
echo "🗄️ Initializing database..."
python init_db.py

# Configure the application with default values
echo "⚙️ Configuring application..."
python configure.py --set-date 2025-10-30 --flight-number "AA-3010" --destination "Padang"

# Check if database was created
if [ -f "rsvp_database.db" ]; then
    echo "✅ Database created successfully"
else
    echo "❌ Database creation failed"
    exit 1
fi

echo "🎉 Deployment completed successfully!"
echo "📝 To start the application, run: python app.py"
echo "🌐 The application will be available on port 5000"