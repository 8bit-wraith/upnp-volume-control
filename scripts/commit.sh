#!/bin/bash

# 🎉 Commit Script with Trisha's Flair! 🎉

# Colorful git magic
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default commit message if not provided
DEFAULT_MESSAGE="🚀 Trisha's Magic Update: Another awesome improvement! 🌈"

# Use provided message or default
COMMIT_MESSAGE="${1:-$DEFAULT_MESSAGE}"

# Stage all changes
git add .

# Commit with message
git commit -m "$COMMIT_MESSAGE"

# Optional: Push to remote (uncomment if needed)
# git push

echo -e "${GREEN}✨ Committed with style! ${YELLOW}${COMMIT_MESSAGE}${NC}"
