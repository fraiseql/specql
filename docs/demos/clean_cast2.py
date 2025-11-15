#!/usr/bin/env python3
with open('installation.cast', 'rb') as f:
    content = f.read()

# Decode and remove empty lines
lines = content.decode('utf-8', errors='replace').split('\n')
clean_lines = [line for line in lines if line.strip()]

with open('installation_clean.cast', 'w') as f:
    f.write('\n'.join(clean_lines))

print(f"Wrote {len(clean_lines)} lines")
