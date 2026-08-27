#!/bin/bash

echo "🚀 Starting Telegram Bots on Railway..."

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --no-cache-dir -r requirements.txt

# Create bots directory
mkdir -p bots

# Run all bots
python dm_bot.py &
python admin_bot.py &
python clone_bot.py &

wait
