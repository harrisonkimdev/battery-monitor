#!/bin/bash
# Build script for Battery Monitor macOS app

set -e  # Exit on error

echo "🧹 Cleaning previous build..."
rm -rf build dist

echo "🔨 Building app..."
/opt/miniconda3/envs/battery-monitor/bin/python setup.py py2app 2>&1 | grep -v "copying file" | grep -v "creating" || {
    # If build fails due to duplicate files, try to fix it
    echo "⚠️  Build failed, attempting to fix duplicate files..."
    
    # Remove problematic vendor directory from build
    if [ -d "build" ]; then
        find build -type d -name "_vendor" -exec rm -rf {} + 2>/dev/null || true
        find build -type d -name "setuptools._vendor*" -exec rm -rf {} + 2>/dev/null || true
    fi
    
    # Try again
    echo "🔨 Retrying build..."
    /opt/miniconda3/envs/battery-monitor/bin/python setup.py py2app
}

if [ -d "dist/Battery Monitor.app" ]; then
    echo "✅ Build completed successfully!"
    
    echo "🔧 Setting up RPATH..."
    install_name_tool -add_rpath @executable_path/../Frameworks \
        "dist/Battery Monitor.app/Contents/MacOS/Battery Monitor" 2>/dev/null || true
    
    install_name_tool -add_rpath @executable_path/../Frameworks \
        "dist/Battery Monitor.app/Contents/MacOS/python" 2>/dev/null || true
    
    echo "✍️  Code signing..."
    codesign --force --deep --sign - "dist/Battery Monitor.app"
    
    echo "🎉 App is ready at: dist/Battery Monitor.app"
    echo "📦 App size: $(du -sh "dist/Battery Monitor.app" | cut -f1)"
else
    echo "❌ Build failed!"
    exit 1
fi

