#!/bin/bash

. .venv/bin/activate

SW_LOG=$1

# not picky, any char will do
if [ -z "$SW_LOG" ]; then
    # semi-production
    uvicorn main:app --host 0.0.0.0 --port 8000 --no-server-header --log-config /home/azureuser/app/config/uvicorn/logging.yaml >> /home/azureuser/app/logs/access.log 2>&1
else
    # debugging
    uvicorn main:app --host 0.0.0.0 --port 8000 --no-server-header --log-config '/home/azureuser/app/config/uvicorn/logging.yaml' --reload
fi

#uvicorn main:app --host 0.0.0.0 --port 8000 --no-server-header >> /var/log/uvicorn/access.log 2>&1

