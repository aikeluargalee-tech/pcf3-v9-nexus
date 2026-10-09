#!/usr/bin/env python3
"""Build root threat-matrix.html mirror from threat-matrix/index.html"""
import sys

with open('threat-matrix/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Update canonical and og:url and self-link for root mirror
content = content.replace(
    '<link rel="canonical" href="./index.html"/>',
    '<link rel="canonical" href="./threat-matrix.html"/>'
)
content = content.replace(
    '<meta property="og:url" content="https://aikeluargalee-tech.github.io/pcf3-v9-nexus/threat-matrix/"/>',
    '<meta property="og:url" content="https://aikeluargalee-tech.github.io/pcf3-v9-nexus/threat-matrix.html"/>'
)
content = content.replace(
    '⚠️ LABS &gt; <a href="./index.html" style="font-weight:800; color:#fff;">MACRO THREAT MATRIX</a>',
    '⚠️ LABS &gt; <a href="./threat-matrix.html" style="font-weight:800; color:#fff;">MACRO THREAT MATRIX</a>'
)

with open('threat-matrix.html', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"threat-matrix.html successfully written! Size: {len(content)} bytes")
