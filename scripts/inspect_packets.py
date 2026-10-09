import sys
import os
import re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

repo = r'C:\Users\aikel\pcf3-v9-nexus'

# 1. Packet 1: index.html (PCF3_LIVE_PACKET_DEFAULT.txt)
p1_path = os.path.join(repo, 'PCF3_LIVE_PACKET_DEFAULT.txt')
if os.path.exists(p1_path):
    with open(p1_path, 'r', encoding='utf-8') as f:
        p1 = f.read()
    print('================================================================================')
    print('PAGE 1: index.html -> DATA PACKET 1 (Master Packet)')
    print('================================================================================')
    lines = p1.splitlines()
    for l in lines[:30]:
        print(l)
    print(f'... [Total Lines: {len(lines)}, Total Characters: {len(p1)}]')

# 2. Packet 2: matrix.html (data2_exporter.js)
p2_path = os.path.join(repo, 'data2_exporter.js')
if os.path.exists(p2_path):
    with open(p2_path, 'r', encoding='utf-8') as f:
        p2 = f.read()
    print('\n================================================================================')
    print('PAGE 2: matrix.html -> DATA PACKET 2 (Plan Review / Tactical Execution Sleeve)')
    print('================================================================================')
    # find where packetLines or template string is constructed
    m2 = re.search(r'var packetLines\s*=\s*\[(.*?)\];', p2, re.DOTALL)
    if m2:
        block = m2.group(1)
        sublines = [s.strip() for s in block.splitlines() if s.strip()][:35]
        for s in sublines:
            print(s)
    else:
        # search for packet string
        print('Searching for packet template in data2_exporter.js...')
        m2_str = re.search(r'var out\s*=\s*\[(.*?)\];', p2, re.DOTALL)
        if m2_str:
            for s in m2_str.group(1).splitlines()[:35]:
                print(s.strip())
        else:
            for line in p2.splitlines()[60:100]:
                print(line)

# 3. Packet 3: quant-radar/index.html
p3_path = os.path.join(repo, 'quant-radar', 'index.html')
if os.path.exists(p3_path):
    with open(p3_path, 'r', encoding='utf-8') as f:
        p3 = f.read()
    print('\n================================================================================')
    print('PAGE 3: quant-radar -> DATA PACKET 3 (Quant Radar)')
    print('================================================================================')
    m3 = re.search(r'const packetLines\s*=\s*\[(.*?)\];', p3, re.DOTALL)
    if m3:
        for s in [line.strip() for line in m3.group(1).splitlines() if line.strip()][:35]:
            print(s)

# 4. Packet 4: liquidity-radar/index.html
p4_path = os.path.join(repo, 'liquidity-radar', 'index.html')
if os.path.exists(p4_path):
    with open(p4_path, 'r', encoding='utf-8') as f:
        p4 = f.read()
    print('\n================================================================================')
    print('PAGE 4: liquidity-radar -> DATA PACKET 4 (Liquidity Radar / Protocol)')
    print('================================================================================')
    m4 = re.search(r'const packetLines\s*=\s*\[(.*?)\];', p4, re.DOTALL)
    if m4:
        for s in [line.strip() for line in m4.group(1).splitlines() if line.strip()][:35]:
            print(s)
