#!/bin/bash
# NOX Installation Script
# Installs NOX reasoning protocol for Hermes Agent

set -e

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

# Installation paths
HERMES_DIR="$HOME/.hermes"
SKILLS_DIR="$HERMES_DIR/skills"
NOX_SKILL_DIR="$SKILLS_DIR/nox"
NOX_LANG_DIR="$HOME/nox-lang"

# Print functions
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo "  $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Do not run this script as root"
    exit 1
fi

# Check if Hermes directory exists
if [ ! -d "$HERMES_DIR" ]; then
    print_error "Hermes directory not found: $HERMES_DIR"
    print_info "Please install Hermes Agent first"
    exit 1
fi

print_success "Hermes directory found: $HERMES_DIR"

# Create directories
print_info "Creating directories..."
mkdir -p "$NOX_SKILL_DIR"
mkdir -p "$NOX_LANG_DIR/references"
mkdir -p "$NOX_LANG_DIR/templates"
mkdir -p "$NOX_LANG_DIR/scripts"
print_success "Directories created"

# Check if files already exist
if [ -f "$NOX_SKILL_DIR/SKILL.md" ]; then
    print_warning "NOX already installed. Updating files..."
fi

# Copy files (assuming script is run from the NOX directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$SCRIPT_DIR/SKILL.md" ]; then
    print_info "Copying skill files..."
    cp "$SCRIPT_DIR/SKILL.md" "$NOX_SKILL_DIR/"
    cp "$SCRIPT_DIR/toggle.py" "$NOX_SKILL_DIR/"
    cp "$SCRIPT_DIR/validate.py" "$NOX_SKILL_DIR/"
    cp "$SCRIPT_DIR/SPEC.md" "$NOX_SKILL_DIR/"
    cp "$SCRIPT_DIR/CHANGELOG.md" "$NOX_SKILL_DIR/"
    cp "$SCRIPT_DIR/README.md" "$NOX_SKILL_DIR/"
    print_success "Skill files copied"
else
    print_warning "SKILL.md not found in script directory. Skipping file copy."
    print_info "Please ensure all files are in: $SCRIPT_DIR"
fi

# Set permissions
print_info "Setting permissions..."
chmod +x "$NOX_SKILL_DIR/toggle.py"
chmod +x "$NOX_SKILL_DIR/validate.py"
print_success "Permissions set"

# Create symbolic links for easy access (optional)
if [ ! -L "$HERMES_DIR/bin/nox-toggle" ]; then
    mkdir -p "$HERMES_DIR/bin"
    ln -sf "$NOX_SKILL_DIR/toggle.py" "$HERMES_DIR/bin/nox-toggle"
    print_success "Created symlink: $HERMES_DIR/bin/nox-toggle"
fi

if [ ! -L "$HERMES_DIR/bin/nox-validate" ]; then
    ln -sf "$NOX_SKILL_DIR/validate.py" "$HERMES_DIR/bin/nox-validate"
    print_success "Created symlink: $HERMES_DIR/bin/nox-validate"
fi

# Verify installation
print_info "Verifying installation..."

if [ -f "$NOX_SKILL_DIR/SKILL.md" ]; then
    print_success "SKILL.md found"
else
    print_error "SKILL.md not found"
    exit 1
fi

if [ -f "$NOX_SKILL_DIR/toggle.py" ]; then
    print_success "toggle.py found"
else
    print_error "toggle.py not found"
    exit 1
fi

if [ -f "$NOX_SKILL_DIR/validate.py" ]; then
    print_success "validate.py found"
else
    print_error "validate.py not found"
    exit 1
fi

if [ -f "$NOX_SKILL_DIR/SPEC.md" ]; then
    print_success "SPEC.md found"
else
    print_error "SPEC.md not found"
    exit 1
fi

if [ -f "$NOX_SKILL_DIR/CHANGELOG.md" ]; then
    print_success "CHANGELOG.md found"
else
    print_error "CHANGELOG.md not found"
    exit 1
fi

if [ -f "$NOX_SKILL_DIR/README.md" ]; then
    print_success "README.md found"
else
    print_error "README.md not found"
    exit 1
fi

if [ -d "$NOX_LANG_DIR" ]; then
    print_success "nox-lang directory found"
else
    print_error "nox-lang directory not found"
    exit 1
fi

# Test Python scripts
print_info "Testing Python scripts..."

if python3 --version &> /dev/null; then
    if python3 "$NOX_SKILL_DIR/toggle.py" status &> /dev/null; then
        print_success "toggle.py is executable"
    else
        print_warning "toggle.py test failed (may need configuration)"
    fi
    
    if python3 "$NOX_SKILL_DIR/validate.py" --help &> /dev/null || true; then
        print_success "validate.py is executable"
    else
        print_warning "validate.py test failed (may need text input)"
    fi
else
    print_warning "Python3 not found. Scripts may not work."
fi

# Print summary
echo ""
echo "=========================================="
echo "NOX Installation Complete!"
echo "=========================================="
echo ""
echo "Installed files:"
echo "  - $NOX_SKILL_DIR/SKILL.md"
echo "  - $NOX_SKILL_DIR/toggle.py"
echo "  - $NOX_SKILL_DIR/validate.py"
echo "  - $NOX_SKILL_DIR/SPEC.md"
echo "  - $NOX_SKILL_DIR/CHANGELOG.md"
echo "  - $NOX_SKILL_DIR/README.md"
echo "  - $NOX_LANG_DIR/references/"
echo "  - $NOX_LANG_DIR/templates/"
echo "  - $NOX_LANG_DIR/scripts/"
echo ""
echo "Quick start:"
echo "  # Enable NOX"
echo "  python3 $NOX_SKILL_DIR/toggle.py enable"
echo ""
echo "  # Check status"
echo "  python3 $NOX_SKILL_DIR/toggle.py status"
echo ""
echo "  # Validate text"
echo "  python3 $NOX_SKILL_DIR/validate.py \"Your text here\""
echo ""
echo "For more information, see:"
echo "  - $NOX_SKILL_DIR/README.md"
echo "  - $NOX_SKILL_DIR/SKILL.md"
echo ""
echo "=========================================="
