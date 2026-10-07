#!/bin/bash
exec python3 -m streamlit run app.py \
  --server.port 3000 \
  --server.address 0.0.0.0 \
  --server.headless true \
  --browser.gatherUsageStats false \
  --server.enableCORS false \
  --server.enableXsrfProtection false
