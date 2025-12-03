#!/bin/bash

# ==========================================
# 🔧 CONFIGURATION
# ==========================================
# Your specific repository URL
REPO_URL="https://github.com/unknownlonewolf9-netizen/ciphereye.git"
DIR_NAME="ciphereye"

# ==========================================
# 🎨 COLORS
# ==========================================
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ==========================================
# 🚀 PRE-FLIGHT CHECKS
# ==========================================
echo -e "${BLUE}Checking system requirements...${NC}"

if ! command -v git &> /dev/null; then
    echo -e "${RED}Error: Git is not installed.${NC}"
    echo "Please install Git: https://git-scm.com/downloads"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed.${NC}"
    echo "Please install Docker Desktop: https://www.docker.com/products/docker-desktop/"
    exit 1
fi

# ==========================================
# 📥 CLONE / UPDATE REPO
# ==========================================
if [ -d "$DIR_NAME" ]; then
    echo -e "${GREEN}📂 Project folder found.${NC} Updating to latest version..."
    cd "$DIR_NAME"
    # Stash local changes to prevent conflicts, pull, then apply stashed changes (optional)
    git stash
    git pull origin main
else
    echo -e "${BLUE}📥 Cloning CipherEye repository...${NC}"
    git clone "$REPO_URL"
    cd "$DIR_NAME"
fi

# ==========================================
# 🐳 LAUNCH DOCKER
# ==========================================
echo ""
echo -e "${BLUE}🚀 Starting System Services...${NC}"
echo "   (This may take a few minutes if running for the first time)"

# Ensure we are using the optimized production settings we built
docker compose up -d --build

# ==========================================
# ✅ SYSTEM STATUS
# ==========================================
echo ""
echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN}      👁️   CIPHEREYE IS ONLINE   👁️      ${NC}"
echo -e "${GREEN}=============================================${NC}"
echo ""
echo -e "🛡️  ${BLUE}Admin Panel:${NC}    http://localhost:8501"
echo -e "🎮  ${BLUE}Player Arena:${NC}   http://localhost:8502"
echo ""
echo -e "${GREEN}=============================================${NC}"
echo "Press [ENTER] to stop the server and clean up..."
read

# ==========================================
# 🛑 SHUTDOWN
# ==========================================
echo -e "${RED}🛑 Shutting down services...${NC}"
docker compose down

echo "✨ System stopped. Goodbye!"
