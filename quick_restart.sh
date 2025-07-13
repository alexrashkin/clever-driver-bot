#!/bin/bash

echo "⚡ Быстрый перезапуск Flask..."

ssh root@194.87.236.174 << 'EOF'
    cd /opt/driver-bot
    git pull origin main
    pkill -f "python.*run_web.py"
    sleep 2
    nohup python run_web.py > web.log 2>&1 &
    sleep 3
    curl -s http://localhost:5000/test
EOF

echo "✅ Flask перезапущен!" 