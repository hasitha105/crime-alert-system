#!/bin/bash

# Upgrade pip inside Render's virtual environment
/opt/render/project/src/.venv/bin/pip install --upgrade pip

# Install dependencies inside the virtual environment
/opt/render/project/src/.venv/bin/pip install -r requirements.txt

# Download spaCy model inside the virtual environment
/opt/render/project/src/.venv/bin/python -m spacy download en_core_web_sm
