#!/bin/bash
cd /home/kavia/workspace/code-generation/supporthub-33392-f6bcaf79/ticketing_frontend_workspace/ticketing_frontend
npm run build
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
   exit 1
fi

