#!/usr/bin/env python3
"""Build root absorption-radar.html mirror from absorption-radar/index.html"""
import sys

with open('absorption-radar/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Update canonical and og:url and self-link for root mirror
content = content.replace(
    '<link rel="canonical" href="./index.html"/>',
    '<link rel="canonical" href="./absorption-radar.html"/>'
)
content = content.replace(
    '<meta property="og:url" content="https://aikeluargalee-tech.github.io/pcf3-v9-nexus/absorption-radar/"/>',
    '<meta property="og:url" content="https://aikeluargalee-tech.github.io/pcf3-v9-nexus/absorption-radar.html"/>'
)
content = content.replace(
    '🎯 LABS &gt; <a href="./index.html" style="font-weight:800; color:#fff;">ABSORPTION RADAR PRO</a>',
    '🎯 LABS &gt; <a href="./absorption-radar.html" style="font-weight:800; color:#fff;">ABSORPTION RADAR PRO</a>'
)

with open('absorption-radar.html', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"absorption-radar.html successfully written! Size: {len(content)} bytes")
