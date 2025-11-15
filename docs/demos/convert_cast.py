#!/usr/bin/env python3
import json
import sys

# Read and validate the cast file
with open('installation.cast', 'r') as f:
    lines = [line.strip() for line in f if line.strip()]
    
print(f"Total lines: {len(lines)}")
print(f"First line (header): {lines[0][:100]}...")
print(f"Second line (first frame): {lines[1]}")
print(f"Last line: {lines[-1]}")

# Try to parse each line
for i, line in enumerate(lines):
    try:
        json.loads(line)
    except json.JSONDecodeError as e:
        print(f"Error at line {i+1}: {e}")
        print(f"Content: {line[:100]}")
        break
else:
    print("All lines are valid JSON!")
