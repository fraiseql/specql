#!/usr/bin/env python3
with open('installation.cast', 'r') as f:
    lines = [line for line in f if line.strip()]

with open('installation_clean.cast', 'w') as f:
    f.writelines(lines)

print(f"Wrote {len(lines)} lines to installation_clean.cast")
