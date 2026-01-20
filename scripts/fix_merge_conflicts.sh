#!/bin/bash
# Script to fix merge conflicts in Python files on the server

echo "Fixing merge conflicts in Python files..."

# Find and remove merge conflict markers from Python files
find app -name "*.py" -type f -exec grep -l "<<<<<<< Updated upstream" {} \; | while read file; do
    echo "Fixing conflicts in: $file"
    
    # Remove conflict markers and keep the "Updated upstream" version (the newer version)
    # This removes everything from <<<<<<< to =======, and removes >>>>>>> line
    sed -i '/<<<<<<< Updated upstream/,/=======/d' "$file"
    sed -i '/>>>>>>> Stashed changes/d' "$file"
    sed -i '/>>>>>>> .*/d' "$file"
    
    echo "Fixed: $file"
done

echo "Merge conflicts fixed. Please review the files and commit if needed."

