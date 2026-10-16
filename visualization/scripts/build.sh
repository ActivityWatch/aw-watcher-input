#!/bin/bash
# Build script for Unix/Linux systems

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

function build() {
    echo -e "${GREEN}Building project...${NC}"
    
    # Create dist directory if it doesn't exist
    mkdir -p dist
    
    # Build bundle.js using browserify
    echo -e "${YELLOW}Building bundle.js...${NC}"
    if command -v browserify &> /dev/null; then
        browserify src/index.js -o dist/bundle.js
        echo -e "${GREEN}✓ bundle.js built successfully${NC}"
    else
        echo -e "${RED}✗ browserify not found. Please install it with: npm install -g browserify${NC}"
        exit 1
    fi
    
    # Build index.html using pug
    echo -e "${YELLOW}Building index.html...${NC}"
    if command -v pug &> /dev/null; then
        pug src/index.pug -o dist/
        echo -e "${GREEN}✓ index.html built successfully${NC}"
    else
        echo -e "${RED}✗ pug not found. Please install it with: npm install -g pug-cli${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Build completed successfully!${NC}"
}

function clean() {
    echo -e "${YELLOW}Cleaning build artifacts...${NC}"
    
    if [ -d "dist" ]; then
        rm -rf dist
        echo -e "${GREEN}✓ dist directory removed${NC}"
    else
        echo -e "${YELLOW}dist directory doesn't exist, nothing to clean${NC}"
    fi
}

function show_help() {
    echo -e "${CYAN}Usage: ./build.sh [command]${NC}"
    echo ""
    echo -e "${CYAN}Commands:${NC}"
    echo -e "  build    Build the project (default)"
    echo -e "  clean    Remove build artifacts"
    echo -e "  help     Show this help message"
}

# Main script logic
case "${1:-build}" in
    build)
        build
        ;;
    clean)
        clean
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_help
        exit 1
        ;;
esac
