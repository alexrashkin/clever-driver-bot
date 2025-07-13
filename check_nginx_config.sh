#!/bin/bash
echo "🔍 ПРОВЕРКА КОНФИГУРАЦИИ NGINX"
echo "================================"

echo "📋 Конфигурация nginx:"
ssh root@194.87.236.174 "cat /etc/nginx/sites-available/default"

echo ""
echo "📋 Проверка синтаксиса:"
ssh root@194.87.236.174 "nginx -t"

echo ""
echo "📋 Статус nginx:"
ssh root@194.87.236.174 "systemctl status nginx --no-pager" 