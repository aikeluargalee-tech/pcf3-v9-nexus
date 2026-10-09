#!/usr/bin/env python3
"""Build root sweep-desk.html mirror from sweep-desk/index.html"""
import sys

with open('sweep-desk/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Update canonical and og:url and self-link for root mirror
content = content.replace(
    '<link rel="canonical" href="./index.html"/>',
    '<link rel="canonical" href="./sweep-desk.html"/>'
)
content = content.replace(
    '<meta property="og:url" content="https://aikeluargalee-tech.github.io/pcf3-v9-nexus/sweep-desk/"/>',
    '<meta property="og:url" content="https://aikeluargalee-tech.github.io/pcf3-v9-nexus/sweep-desk.html"/>'
)
content = content.replace(
    '🎯 LABS &gt; <a href="./index.html" style="font-weight:800; color:#fff;">SWEEP DESK PRO</a>',
    '🎯 LABS &gt; <a href="./sweep-desk.html" style="font-weight:800; color:#fff;">SWEEP DESK PRO</a>'
)

with open('sweep-desk.html', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"sweep-desk.html successfully written! Size: {len(content)} bytes")
