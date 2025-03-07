#!/bin/bash

# Ensure we're in the repository root by checking for .git directory
if [ ! -d ".git" ]; then
    echo "Error: Must run this script from the repository root."
    echo "Current directory: $(pwd)"
    exit 1
fi

# Run the sync script
uv run scripts/sync.py

# Check if there are changes in the resources directory
if git diff --quiet -- src/bluenumbers/resources; then
    echo "No changes detected in resources."
else
    echo "Changes detected in resources directory."
    echo "Do you want to commit these changes? (y/N)"
    read -r response

    if [[ "$response" =~ ^[Yy]$ ]]; then
        # Add changes to git
        git add src/bluenumbers/resources

        # Create commit message with timestamp
        TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
        COMMIT_MSG="[Automated] Resource sync $TIMESTAMP"

        # Commit the changes
        git commit -m "$COMMIT_MSG"
        echo "Changes committed: $COMMIT_MSG"
    else
        echo "Changes not committed."
    fi
fi
