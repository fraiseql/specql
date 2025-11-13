#!/bin/bash

echo "========================================="
echo "SpecQL Java/JDT Setup Verification"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0

# Test 1: Java installed
echo -n "1. Java runtime (java)... "
if command -v java &> /dev/null; then
    VERSION=$(java -version 2>&1 | head -n 1)
    echo -e "${GREEN}PASS${NC} - $VERSION"
    ((PASS++))
else
    echo -e "${RED}FAIL${NC} - java not found in PATH"
    ((FAIL++))
fi

# Test 2: Java compiler
echo -n "2. Java compiler (javac)... "
if command -v javac &> /dev/null; then
    VERSION=$(javac -version 2>&1)
    echo -e "${GREEN}PASS${NC} - $VERSION"
    ((PASS++))
else
    echo -e "${RED}FAIL${NC} - javac not found (JDK required)"
    ((FAIL++))
fi

# Test 3: JAVA_HOME set
echo -n "3. JAVA_HOME environment... "
if [ -n "$JAVA_HOME" ] && [ -d "$JAVA_HOME" ]; then
    echo -e "${GREEN}PASS${NC} - $JAVA_HOME"
    ((PASS++))
else
    echo -e "${YELLOW}WARN${NC} - JAVA_HOME not set (optional but recommended)"
fi

# Test 4: JDK version
echo -n "4. JDK version (≥11)... "
if command -v java &> /dev/null; then
    VERSION=$(java -version 2>&1 | grep -oP 'version "\K[0-9]+' | head -1)
    if [ "$VERSION" -ge 11 ]; then
        echo -e "${GREEN}PASS${NC} - JDK $VERSION"
        ((PASS++))
    else
        echo -e "${RED}FAIL${NC} - JDK $VERSION (need ≥11)"
        ((FAIL++))
    fi
else
    echo -e "${RED}FAIL${NC} - Cannot check version"
    ((FAIL++))
fi

# Test 5: JDT jar exists
echo -n "5. Eclipse JDT JAR... "
if [ -f "lib/jdt/org.eclipse.jdt.core-3.35.0.jar" ]; then
    SIZE=$(ls -lh lib/jdt/org.eclipse.jdt.core-3.35.0.jar | awk '{print $5}')
    echo -e "${GREEN}PASS${NC} - $SIZE"
    ((PASS++))
else
    echo -e "${RED}FAIL${NC} - lib/jdt/org.eclipse.jdt.core-3.35.0.jar not found"
    ((FAIL++))
fi

# Test 6: Py4J jar exists
echo -n "6. Py4J JAR... "
if [ -f "lib/jdt/py4j0.10.9.7.jar" ]; then
    SIZE=$(ls -lh lib/jdt/py4j0.10.9.7.jar | awk '{print $5}')
    echo -e "${GREEN}PASS${NC} - $SIZE"
    ((PASS++))
else
    echo -e "${RED}FAIL${NC} - lib/jdt/py4j0.10.9.7.jar not found"
    ((FAIL++))
fi

# Test 7: Eclipse Equinox Common jar exists
echo -n "7. Eclipse Equinox Common JAR... "
if [ -f "lib/jdt/org.eclipse.equinox.common-3.18.100.jar" ]; then
    SIZE=$(ls -lh lib/jdt/org.eclipse.equinox.common-3.18.100.jar | awk '{print $5}')
    echo -e "${GREEN}PASS${NC} - $SIZE"
    ((PASS++))
else
    echo -e "${RED}FAIL${NC} - lib/jdt/org.eclipse.equinox.common-3.18.100.jar not found"
    ((FAIL++))
fi

# Test 8: JDT wrapper source
echo -n "8. JDT wrapper source... "
if [ -f "lib/jdt/JDTWrapper.java" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}FAIL${NC} - lib/jdt/JDTWrapper.java not found"
    ((FAIL++))
fi

# Test 9: JDT wrapper compiled
echo -n "9. JDT wrapper compiled... "
if [ -f "lib/jdt/JDTWrapper.class" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASS++))
else
    echo -e "${YELLOW}WARN${NC} - Not compiled yet"
    echo "     Run: cd lib/jdt && javac -cp org.eclipse.jdt.core-3.35.0.jar:py4j0.10.9.7.jar:org.eclipse.equinox.common-3.18.100.jar:. JDTWrapper.java"
fi

# Test 10: Py4J installed
echo -n "10. Py4J Python library... "
if uv run python -c "import py4j" 2>/dev/null; then
    echo -e "${GREEN}PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}FAIL${NC} - Run: uv sync"
    ((FAIL++))
fi

echo ""
echo "========================================="
echo -e "Results: ${GREEN}$PASS passed${NC}, ${RED}$FAIL failed${NC}"
echo "========================================="
echo ""

if [ $FAIL -eq 0 ] && [ $PASS -ge 8 ]; then
    echo -e "${GREEN}✓ Java/JDT setup complete!${NC}"
    echo ""
    echo "You can now use Java reverse engineering features:"
    echo "  uv run specql reverse java_entities/Contact.java --output entities/"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Setup incomplete${NC}"
    echo ""
    echo "Next steps:"
    if [ $FAIL -gt 0 ]; then
        echo "  1. Install JDK 11+ for your platform:"
        echo "     - Ubuntu/Debian: sudo apt install openjdk-17-jdk"
        echo "     - macOS: brew install openjdk@17"
        echo "     - Windows: choco install temurin17"
        echo ""
    fi
    if [ ! -f "lib/jdt/JDTWrapper.class" ]; then
        echo "  2. Compile JDT wrapper:"
        echo "     cd lib/jdt"
        echo "     javac -cp org.eclipse.jdt.core-3.35.0.jar:py4j0.10.9.7.jar:org.eclipse.equinox.common-3.18.100.jar:. JDTWrapper.java"
        echo ""
    fi
    echo "See docs/JAVA_SETUP.md for detailed instructions."
    echo ""
    exit 1
fi
