# Java Development Kit (JDK) Setup for SpecQL

**Required for**: Java reverse engineering and JPA pattern analysis

SpecQL uses Eclipse JDT (Java Development Tools) for parsing Java source code and extracting entity patterns from JPA-annotated classes. This requires a working JDK installation.

---

## 📋 Requirements

- **JDK 11 or later** (JDK 17 LTS recommended)
- Eclipse JDT Core JAR (included in `lib/jdt/`)
- Py4J library (auto-installed with SpecQL)

---

## 🚀 Quick Setup

### Linux (Ubuntu/Debian)

```bash
# Install OpenJDK 17
sudo apt update
sudo apt install openjdk-17-jdk

# Verify installation
java -version

# Set JAVA_HOME (add to ~/.bashrc or ~/.zshrc)
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

# Compile JDT wrapper
cd /home/lionel/code/specql/lib/jdt
javac -cp org.eclipse.jdt.core-3.35.0.jar:. JDTWrapper.java
```

### macOS

```bash
# Install OpenJDK via Homebrew
brew install openjdk@17

# Link it
sudo ln -sfn /opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk-17.jdk

# Set JAVA_HOME (add to ~/.zshrc)
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
export PATH=$JAVA_HOME/bin:$PATH

# Verify
java -version

# Compile JDT wrapper
cd /path/to/specql/lib/jdt
javac -cp org.eclipse.jdt.core-3.35.0.jar:. JDTWrapper.java
```

### Windows

```powershell
# Download and install JDK 17 from:
# https://adoptium.net/temurin/releases/

# Or using Chocolatey:
choco install temurin17

# Set JAVA_HOME (System Environment Variables)
# JAVA_HOME = C:\Program Files\Eclipse Adoptium\jdk-17.0.x
# PATH = %JAVA_HOME%\bin;%PATH%

# Verify
java -version

# Compile JDT wrapper
cd C:\path\to\specql\lib\jdt
javac -cp "org.eclipse.jdt.core-3.35.0.jar;." JDTWrapper.java
```

---

## 🔧 Detailed Setup

### Step 1: Check if JDK is Already Installed

```bash
# Check Java version
java -version

# Check if javac (compiler) is available
javac -version

# Check JAVA_HOME
echo $JAVA_HOME
```

**Expected Output** (JDK 17):
```
openjdk version "17.0.x" 2023-xx-xx
OpenJDK Runtime Environment (build 17.0.x+x)
OpenJDK 64-Bit Server VM (build 17.0.x+x, mixed mode, sharing)
```

### Step 2: Install JDK (if needed)

#### Ubuntu/Debian
```bash
# OpenJDK 17 (recommended)
sudo apt update
sudo apt install openjdk-17-jdk openjdk-17-jre

# Alternative: Oracle JDK (requires manual download)
# Download from: https://www.oracle.com/java/technologies/downloads/
```

#### Arch Linux
```bash
sudo pacman -S jdk-openjdk
```

#### Fedora/RHEL/CentOS
```bash
sudo dnf install java-17-openjdk-devel
```

#### macOS with Homebrew
```bash
# Install OpenJDK 17
brew install openjdk@17

# Create symlink (required for macOS to recognize it)
sudo ln -sfn /opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk \
  /Library/Java/JavaVirtualMachines/openjdk-17.jdk
```

#### macOS with SDKMAN
```bash
# Install SDKMAN
curl -s "https://get.sdkman.io" | bash
source "$HOME/.sdkman/bin/sdkman-init.sh"

# Install JDK
sdk install java 17.0.9-tem
sdk default java 17.0.9-tem
```

### Step 3: Set JAVA_HOME

#### Linux/macOS (bash)

Add to `~/.bashrc` or `~/.bash_profile`:
```bash
# For OpenJDK on Ubuntu/Debian
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# For macOS Homebrew
export JAVA_HOME=$(/usr/libexec/java_home -v 17)

# Add to PATH
export PATH=$JAVA_HOME/bin:$PATH
```

Then reload:
```bash
source ~/.bashrc
```

#### Linux/macOS (zsh)

Add to `~/.zshrc`:
```bash
export JAVA_HOME=$(/usr/libexec/java_home -v 17)  # macOS
# OR
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64  # Linux

export PATH=$JAVA_HOME/bin:$PATH
```

Then reload:
```bash
source ~/.zshrc
```

#### Windows

1. Right-click **This PC** → **Properties**
2. Click **Advanced system settings**
3. Click **Environment Variables**
4. Under **System variables**, click **New**:
   - Variable name: `JAVA_HOME`
   - Variable value: `C:\Program Files\Eclipse Adoptium\jdk-17.0.x`
5. Edit **Path** variable, add: `%JAVA_HOME%\bin`
6. Click **OK** to save

### Step 4: Compile JDT Wrapper

The JDT wrapper is a small Java program that bridges Python (via Py4J) to Eclipse JDT.

```bash
cd lib/jdt

# Linux/macOS
javac -cp org.eclipse.jdt.core-3.35.0.jar:py4j0.10.9.7.jar:org.eclipse.equinox.common-3.18.100.jar:. JDTWrapper.java

# Windows
javac -cp "org.eclipse.jdt.core-3.35.0.jar;py4j0.10.9.7.jar;org.eclipse.equinox.common-3.18.100.jar;." JDTWrapper.java

# Verify compilation
ls -la JDTWrapper.class  # Should exist (929 bytes)
```

### Step 5: Test Java Reverse Engineering

```bash
# Go back to project root
cd ../..

# Test Java parsing
uv run python -c "
from src.reverse_engineering.java.jdt_bridge import JDTBridge

bridge = JDTBridge()
java_code = '''
@Entity
public class Contact {
    @Id
    private Long id;

    @Column(nullable = false)
    private String email;
}
'''

ast = bridge.parse_java(java_code)
print('✓ JDT bridge working!' if ast else '✗ Failed')
"
```

**Expected Output**:
- If JDK is properly installed: `✓ JDT bridge working!`
- If JDK is missing: `Warning: JDT bridge initialization failed, using mock implementation`

---

## 🧪 Verification Script

Run this script to verify your setup:

```bash
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
    echo -e "${YELLOW}WARN${NC} - JAVA_HOME not set (optional)"
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

# Test 6: JDT wrapper compiled
echo -n "6. JDT wrapper compiled... "
if [ -f "lib/jdt/JDTWrapper.class" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASS++))
else
    echo -e "${YELLOW}WARN${NC} - Run: cd lib/jdt && javac -cp org.eclipse.jdt.core-3.35.0.jar:. JDTWrapper.java"
fi

# Test 7: Py4J installed
echo -n "7. Py4J Python library... "
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

if [ $FAIL -eq 0 ] && [ $PASS -ge 5 ]; then
    echo -e "${GREEN}✓ Java/JDT setup complete!${NC}"
    echo "You can now use Java reverse engineering features."
    exit 0
else
    echo -e "${RED}✗ Setup incomplete${NC}"
    echo ""
    echo "Next steps:"
    [ $FAIL -gt 0 ] && echo "  - Install JDK 11+ (see above for your platform)"
    [ ! -f "lib/jdt/JDTWrapper.class" ] && echo "  - Compile JDT wrapper"
    exit 1
fi
```

Save this as `scripts/verify_java_setup.sh` and run:
```bash
chmod +x scripts/verify_java_setup.sh
./scripts/verify_java_setup.sh
```

---

## 🔍 Troubleshooting

### Issue: "java: command not found"

**Solution**: JDK not installed or not in PATH
- Install JDK (see Step 2 above)
- Add to PATH: `export PATH=$JAVA_HOME/bin:$PATH`

### Issue: "javac: command not found"

**Solution**: Only JRE installed, need JDK
- JRE (Java Runtime) is not enough - you need JDK (Java Development Kit)
- Install the `-jdk` package, not just `-jre`

### Issue: "JAVA_HOME not set"

**Solution**: Set environment variable
```bash
# Find Java installation
whereis java
# or
which java

# Set JAVA_HOME (add to shell profile)
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
```

### Issue: "UnsupportedClassVersionError"

**Solution**: JDT JAR requires Java 11+
- Check your Java version: `java -version`
- Upgrade to JDK 11 or later

### Issue: "JDTWrapper.java compilation failed"

**Solution**: Ensure all JARs are in classpath
```bash
# Linux/macOS - use colon (:)
javac -cp org.eclipse.jdt.core-3.35.0.jar:py4j0.10.9.7.jar:org.eclipse.equinox.common-3.18.100.jar:. JDTWrapper.java

# Windows - use semicolon (;)
javac -cp "org.eclipse.jdt.core-3.35.0.jar;py4j0.10.9.7.jar;org.eclipse.equinox.common-3.18.100.jar;." JDTWrapper.java
```

**Missing JARs?** Download from Maven Central:
```bash
cd lib/jdt
curl -L -o py4j0.10.9.7.jar https://repo1.maven.org/maven2/net/sf/py4j/py4j/0.10.9.7/py4j-0.10.9.7.jar
curl -L -o org.eclipse.equinox.common-3.18.100.jar https://repo1.maven.org/maven2/org/eclipse/platform/org.eclipse.equinox.common/3.18.100/org.eclipse.equinox.common-3.18.100.jar
```

### Issue: "JDT bridge initialization failed"

**Fallback Behavior**: SpecQL automatically falls back to mock implementation
- Java parsing still works (basic regex-based)
- Limited accuracy compared to full JDT AST
- No error - just a warning message

**To Fix**:
1. Ensure JDK is installed and in PATH
2. Compile JDTWrapper.class
3. Verify with verification script

---

## 📦 What's Included

SpecQL includes these Java-related files:

```
lib/jdt/
├── org.eclipse.jdt.core-3.35.0.jar           # Eclipse JDT Core (4.1MB)
├── py4j0.10.9.7.jar                          # Py4J Java Gateway (122KB)
├── org.eclipse.equinox.common-3.18.100.jar   # Eclipse Core Runtime (151KB)
├── JDTWrapper.java                           # Python-Java bridge source
└── JDTWrapper.class                          # Compiled wrapper (after setup)
```

**Eclipse JDT Core** (org.eclipse.jdt.core):
- Version: 3.35.0
- License: Eclipse Public License 2.0
- Purpose: Parse Java source code to AST
- Source: https://www.eclipse.org/jdt/

**Py4J**:
- Version: 0.10.9.7 (JAR) / 0.10.9+ (Python library)
- License: BSD 3-Clause
- Purpose: Bridge Python and Java processes
- Source: https://www.py4j.org/

**Eclipse Equinox Common**:
- Version: 3.18.100
- License: Eclipse Public License 2.0
- Purpose: Core runtime interfaces (IProgressMonitor, etc.)
- Source: https://www.eclipse.org/equinox/

---

## 🎯 Usage in SpecQL

Once JDK is set up, you can use Java reverse engineering:

```bash
# Reverse engineer Java JPA entities
uv run specql reverse java_entities/Contact.java --output entities/

# Batch process
uv run specql reverse src/main/java/entities/*.java --output entities/

# With verbose output
uv run specql reverse Contact.java --verbose --show-ast
```

**Example Java Input** (`Contact.java`):
```java
@Entity
@Table(name = "contacts")
public class Contact {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 100)
    private String email;

    @ManyToOne
    @JoinColumn(name = "company_id")
    private Company company;

    @Enumerated(EnumType.STRING)
    private ContactStatus status;
}
```

**Generated SpecQL Output** (`contact.yaml`):
```yaml
entity: Contact
schema: public
fields:
  email:
    type: email
    required: true
  company:
    type: ref(Company)
  status:
    type: enum
    values: [LEAD, PROSPECT, CUSTOMER]
```

---

## 🚫 Working Without JDK

If you don't need Java reverse engineering, you can skip JDK installation:

- SpecQL core features work fine without JDK
- Schema generation, actions, CLI all work
- Only Java parsing uses mock implementation
- No errors, just reduced accuracy for Java files

To verify mock mode is working:
```bash
uv run python -c "
from src.reverse_engineering.java.jdt_bridge import JDTBridge
bridge = JDTBridge()
print('Mock mode:', hasattr(bridge, 'mock_mode'))
"
```

---

## 📚 Additional Resources

- **JDK Downloads**: https://adoptium.net/
- **Eclipse JDT**: https://www.eclipse.org/jdt/
- **Py4J Documentation**: https://www.py4j.org/
- **OpenJDK**: https://openjdk.org/

---

## ✅ Summary

| Requirement | Purpose | Required? |
|-------------|---------|-----------|
| JDK 11+ | Compile Java code, run JDT | Yes (for Java reverse engineering) |
| JAVA_HOME | Environment variable | Recommended |
| Eclipse JDT JAR | Parse Java to AST | Included in `lib/jdt/` |
| Py4J JAR | Java gateway library | Included in `lib/jdt/` |
| Eclipse Equinox Common JAR | Core runtime interfaces | Included in `lib/jdt/` |
| JDTWrapper.class | Bridge to Python | Compile after JDK install |
| Py4J Python library | Python-Java communication | Auto-installed with SpecQL |

**Minimum Steps**:
1. Install JDK 11+
2. Set JAVA_HOME
3. Compile JDTWrapper
4. Test with verification script

**Time to set up**: ~5 minutes

---

**Last Updated**: 2025-11-13
**SpecQL Version**: 0.4.0+
