#!/bin/bash

echo "🚀 Starting Telegram Bots on Railway..."

# Create bots directory
mkdir -p bots

# Run all bots in background
python dm_bot.py &
python admin_bot.py &
python clone_bot.py &

# Keep the process running
wait
