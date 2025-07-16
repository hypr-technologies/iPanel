#!/bin/bash

# Script to remove external dependencies from bt.cn and aapanel.com
# This script will replace all references with GitHub-based alternatives

echo "Removing external dependencies from iPanel..."

# Define replacement URLs
GITHUB_REPO="https://github.com/hypr-technologies/iPanel"
GITHUB_RAW="https://raw.githubusercontent.com/hypr-technologies/iPanel/main"
GITHUB_RELEASES="https://github.com/hypr-technologies/iPanel/releases/latest/download"
GITHUB_CDN="https://cdn.jsdelivr.net/gh/hypr-technologies/iPanel@main"

# Function to replace bt.cn references
replace_bt_cn_references() {
    local file="$1"
    if [[ -f "$file" ]]; then
        # Replace bt.cn download URLs
        sed -i "s|http://download\.bt\.cn|$GITHUB_RELEASES|g" "$file"
        sed -i "s|https://download\.bt\.cn|$GITHUB_RELEASES|g" "$file"
        sed -i "s|http://www\.bt\.cn|$GITHUB_REPO|g" "$file"
        sed -i "s|https://www\.bt\.cn|$GITHUB_REPO|g" "$file"
        sed -i "s|http://dg[0-9]\.bt\.cn|$GITHUB_RELEASES|g" "$file"
        sed -i "s|https://dg[0-9]\.bt\.cn|$GITHUB_RELEASES|g" "$file"
        sed -i "s|http://node\.bt\.cn|$GITHUB_RELEASES|g" "$file"
        sed -i "s|https://node\.bt\.cn|$GITHUB_RELEASES|g" "$file"
        
        # Replace API calls
        sed -i "s|/ip|/ip|g" "$file"
        sed -i "s|||g" "$file"
        sed -i "s|||g" "$file"
        
        echo "Updated bt.cn references in $file"
    fi
}

# Function to replace aapanel.com references
replace_aapanel_references() {
    local file="$1"
    if [[ -f "$file" ]]; then
        # Replace aapanel.com URLs
        sed -i "s|https://www\.aapanel\.com|$GITHUB_REPO|g" "$file"
        sed -i "s|http://www\.aapanel\.com|$GITHUB_REPO|g" "$file"
        sed -i "s|https://brandnew\.aapanel\.com|$GITHUB_REPO|g" "$file"
        sed -i "s|https://console\.aapanel\.com|$GITHUB_REPO|g" "$file"
        sed -i "s|https://node\.aapanel\.com|$GITHUB_RELEASES|g" "$file"
        sed -i "s|http://node\.aapanel\.com|$GITHUB_RELEASES|g" "$file"
        
        # Replace API endpoints
        sed -i "s|||g" "$file"
        sed -i "s|||g" "$file"
        sed -i "s|||g" "$file"
        
        echo "Updated aapanel.com references in $file"
    fi
}

# Function to update text references
replace_text_references() {
    local file="$1"
    if [[ -f "$file" ]]; then
        # Replace text references in language files
        sed -i 's|"bt\.cn"|"GitHub"|g' "$file"
        sed -i 's|"www\.bt\.cn"|"github.com/hypr-technologies/iPanel"|g' "$file"
        sed -i 's|"aapanel\.com"|"github.com/hypr-technologies/iPanel"|g' "$file"
        sed -i 's|"forum\.aapanel\.com"|"github.com/hypr-technologies/iPanel/issues"|g' "$file"
        
        # Replace branding
        sed -i 's|"aaPanel"|"iPanel"|g' "$file"
        sed -i 's|"BT-Panel"|"iPanel"|g' "$file"
        sed -i 's|"宝塔"|"iPanel"|g' "$file"
        
        echo "Updated text references in $file"
    fi
}

# Main processing
echo "Processing language files..."
find . -name "*.json" -path "*/lang/*" | while read -r file; do
    replace_bt_cn_references "$file"
    replace_aapanel_references "$file"
    replace_text_references "$file"
done

echo "Processing configuration files..."
find . -name "*.json" -path "*/config/*" | while read -r file; do
    replace_bt_cn_references "$file"
    replace_aapanel_references "$file"
done

echo "Processing data files..."
find . -name "*.json" -path "*/data/*" | while read -r file; do
    replace_bt_cn_references "$file"
    replace_aapanel_references "$file"
done

echo "Processing shell scripts..."
find . -name "*.sh" | while read -r file; do
    replace_bt_cn_references "$file"
    replace_aapanel_references "$file"
done

echo "Processing Python files..."
find . -name "*.py" | while read -r file; do
    replace_bt_cn_references "$file"
    replace_aapanel_references "$file"
done

echo "Processing PHP files..."
find . -name "*.php" | while read -r file; do
    replace_bt_cn_references "$file"
    replace_aapanel_references "$file"
done

echo "Processing HTML/JS files..."
find . -name "*.html" -o -name "*.js" | while read -r file; do
    replace_bt_cn_references "$file"
    replace_aapanel_references "$file"
done

echo "External dependencies removal complete!"
echo "All references to bt.cn and aapanel.com have been replaced with GitHub alternatives."


