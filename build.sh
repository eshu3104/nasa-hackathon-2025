#!/bin/bash
# Render build script

echo "Installing Python dependencies..."
pip install -r requirements_render.txt

echo "Checking model files..."
ls -la models/ || echo "Models directory not found"

echo "Build complete!"