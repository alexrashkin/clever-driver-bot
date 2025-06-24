#!/bin/bash

echo "Testing toggle_tracking endpoint..."
curl -X POST http://localhost:8000/api/toggle_tracking/ \
  -H "Content-Type: application/json" \
  -d '{"is_tracking": true}'

echo -e "\n\nTesting location endpoint..."
curl "http://localhost:8000/api/location/?latitude=55.676803&longitude=37.52351"

echo -e "\n\nTesting toggle_tracking endpoint again..."
curl -X POST http://localhost:8000/api/toggle_tracking/ \
  -H "Content-Type: application/json" \
  -d '{"is_tracking": false}' 