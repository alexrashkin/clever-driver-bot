#!/bin/bash

echo "=== Testing Views ==="

cd /opt/driver
source venv/bin/activate

echo "Testing main_page view..."
python manage.py shell -c "
from django.test import RequestFactory
from driver.views import main_page
import json

factory = RequestFactory()
request = factory.get('/')
try:
    response = main_page(request)
    print(f'Status: {response.status_code}')
    print(f'Content: {response.content[:200]}')
except Exception as e:
    print(f'Error: {e}')
"

echo "Testing toggle_tracking view..."
python manage.py shell -c "
from django.test import RequestFactory
from driver.views import toggle_tracking
import json

factory = RequestFactory()
request = factory.post('/api/toggle_tracking/', 
                      data=json.dumps({'is_tracking': True}),
                      content_type='application/json')
try:
    response = toggle_tracking(request)
    print(f'Status: {response.status_code}')
    print(f'Content: {response.content}')
except Exception as e:
    print(f'Error: {e}')
"

echo "=== View testing complete ===" 