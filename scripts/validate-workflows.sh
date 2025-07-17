#!/bin/bash

# GitHub Actions Workflow Validation Script
# This script validates YAML syntax for all workflow files

set -e

echo "🔍 Validating GitHub Actions workflow files..."
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counter for validation results
total_files=0
valid_files=0
invalid_files=0

# Function to validate a single YAML file
validate_yaml() {
    local file="$1"
    echo -n "Validating $file... "
    
    if python3 -c "
import yaml
import sys
try:
    with open('$file', 'r') as f:
        yaml.safe_load(f)
    print('✅ Valid')
    sys.exit(0)
except yaml.YAMLError as e:
    print(f'❌ Invalid: {e}')
    sys.exit(1)
except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
"; then
        ((valid_files++))
        return 0
    else
        ((invalid_files++))
        return 1
    fi
}

# Find and validate all workflow files
workflow_dir=".github/workflows"

if [ ! -d "$workflow_dir" ]; then
    echo -e "${RED}❌ Workflow directory not found: $workflow_dir${NC}"
    exit 1
fi

echo "Scanning workflow directory: $workflow_dir"
echo ""

# Validate each .yml and .yaml file
for file in "$workflow_dir"/*.yml "$workflow_dir"/*.yaml; do
    if [ -f "$file" ]; then
        ((total_files++))
        validate_yaml "$file"
    fi
done

echo ""
echo "================================================"
echo "📊 Validation Summary:"
echo -e "Total files: ${YELLOW}$total_files${NC}"
echo -e "Valid files: ${GREEN}$valid_files${NC}"
echo -e "Invalid files: ${RED}$invalid_files${NC}"

if [ $invalid_files -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 All workflow files are valid!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Commit the changes to your repository"
    echo "2. Create a new release to test the workflows"
    echo "3. Monitor the GitHub Actions page for execution"
    exit 0
else
    echo ""
    echo -e "${RED}❌ Some workflow files have validation errors.${NC}"
    echo "Please fix the errors before proceeding."
    exit 1
fi
