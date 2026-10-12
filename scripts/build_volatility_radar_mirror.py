#!/usr/bin/env python3
"""Build root volatility-radar.html mirror from volatility-radar/index.html"""
import sys

with open('volatility-radar/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Update canonical and og:url and self-link for root mirror
content = content.replace(
    '<link rel="canonical" href="./index.html"/>',
    '<link rel="canonical" href="./volatility-radar.html"/>'
)
content = content.replace(
    '<meta property="og:url" content="https://aikeluargalee-tech.github.io/pcf3-v9-nexus/volatility-radar/"/>',
    '<meta property="og:url" content="https://aikeluargalee-tech.github.io/pcf3-v9-nexus/volatility-radar.html"/>'
)
content = content.replace(
    '⚡ LABS &gt; <a href="./index.html" style="font-weight:800; color:#fff;">VOLATILITY RADAR PRO</a>',
    '⚡ LABS &gt; <a href="./volatility-radar.html" style="font-weight:800; color:#fff;">VOLATILITY RADAR PRO</a>'
)

# Convert relative parent directory links ../ to ./ for root mirror
content = content.replace('href="../', 'href="./')

with open('volatility-radar.html', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"volatility-radar.html successfully written! Size: {len(content)} bytes")
