#!/bin/bash
# Render Docker build script

echo "🚀 Starting NASA Skynet Backend build..."

# Check if we're in Docker build context
if [ -f "/.dockerenv" ]; then
    echo "📦 Running in Docker container"
else
    echo "🔧 Running in Render build environment"
fi

# Verify Python version
python --version

# Check if model files exist
if [ -d "models" ]; then
    echo "✅ Models directory found"
    echo "📁 Model files:"
    ls -la models/ | head -10
else
    echo "⚠️  Models directory not found"
fi

# Check requirements
if [ -f "requirements_render.txt" ]; then
    echo "✅ Requirements file found"
    echo "📋 Installing dependencies..."
    pip install -r requirements_render.txt
else
    echo "❌ Requirements file not found"
    exit 1
fi

# Verify critical imports
echo "🔍 Testing critical imports..."
python -c "
try:
    import flask
    import numpy
    import sklearn
    import openai
    print('✅ All critical dependencies imported successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

echo "🎉 Build completed successfully!"