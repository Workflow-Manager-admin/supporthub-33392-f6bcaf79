#!/bin/bash
cd /home/kavia/workspace/code-generation/supporthub-33392-f6bcaf79/ticketing_backend_workspace/ticketing_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

