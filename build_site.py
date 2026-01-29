import os
import json
import shutil
import re
import html
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# Configuration
INPUT_DIR = 'input'
OUTPUT_DIR = 'docs'
DB_DIR = 'db'
TEMPLATE_DIR = 'templates'
SITE_URL = "https://instructionsets.com"

# Ensure output directory exists
if os.path.exists(OUTPUT_DIR):
    shutil.rmtree(OUTPUT_DIR)
os.makedirs(OUTPUT_DIR)
os.makedirs(DB_DIR, exist_ok=True)

def load_data():
    master_db = {}
    seen_hashes = set() # Track unique signatures to prevent exact duplicates
    
    # Read all JSON files in the input directory
    if not os.path.exists(INPUT_DIR):
        print(f"Warning: Input directory '{INPUT_DIR}' not found.")
        return master_db

    for filename in os.listdir(INPUT_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(INPUT_DIR, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    
                    # Merge into master_db grouped by Architecture
                    for inst in data.get('instructions', []):
                        arch = inst.get('architecture', 'Unknown')
                        
                        # Deduplication Logic
                        signature = (
                            inst.get('mnemonic', '').strip(),
                            inst.get('syntax', '').strip(),
                            inst.get('encoding', {}).get('hex_opcode', '').strip()
                        )
                        
                        if signature in seen_hashes:
                            continue
                        
                        seen_hashes.add(signature)
                        
                        if arch not in master_db:
                            master_db[arch] = []
                        master_db[arch].append(inst)
            except Exception as e:
                print(f"Error reading {filename}: {e}")
                
    return master_db

def parse_encoding(pattern_str):
    if not pattern_str or not isinstance(pattern_str, str):
        return []
    parts = [p.strip() for p in pattern_str.split('|') if p.strip()]
    return parts

def create_linkifier(mnemonic_to_url):
    sorted_keys = sorted(mnemonic_to_url.keys(), key=len, reverse=True)
    escaped_keys = [re.escape(k) for k in sorted_keys]
    pattern_str = r'\b(' + '|'.join(escaped_keys) + r')\b'
    pattern = re.compile(pattern_str)

    def linkify(text):
        if not text: return ""
        def replace(match):
            key = match.group(0)
            url = mnemonic_to_url.get(key)
            return f'<a href="{url}">{key}</a>'
        return pattern.sub(replace, text)
    
    return linkify

def get_instruction_category(inst):
    """
    Determines the sidebar grouping category for an instruction
    based on Architecture and Extension/Mnemonic.
    """
    arch = inst.get('architecture', '')
    ext = inst.get('extension', '')
    mnemonic = inst.get('mnemonic', '')

    # --- PowerISA Categories ---
    if arch == 'PowerISA':
        if 'Prefixed' in ext: return 'Prefixed (64-bit)'
        if 'VSX' in ext: return 'Vector-Scalar (VSX)'
        if 'VMX' in ext or 'AltiVec' in ext: return 'Vector (VMX/AltiVec)'
        if 'Float' in ext or mnemonic.startswith('f'): return 'Floating Point'
        if mnemonic.startswith('b') or mnemonic == 'sc' or mnemonic == 'trap': return 'Branch & Control'
        if mnemonic.startswith('cmp') or mnemonic.startswith('cr') or mnemonic == 'mtcrf': return 'Comparison & CR'
        if mnemonic.startswith('l') or mnemonic.startswith('st'): return 'Load & Store'
        if mnemonic.startswith('dcb') or mnemonic.startswith('icb'): return 'Cache Management'
        return 'Base Integer'

    # --- ARMv8 / ARMv9 Categories ---
    if arch.startswith('ARM'):
        # Normalize checks to handle mixed case inputs
        ext_u = ext.upper()
        mnem_l = mnemonic.lower()
        
        if 'SVE' in ext_u: return 'SVE (Scalable Vector)'
        if 'SME' in ext_u: return 'SME (Matrix Extensions)'
        if 'NEON' in ext_u or 'SIMD' in ext_u: return 'Advanced SIMD (Neon)'
        if 'F.P.' in ext_u or 'FLOAT' in ext_u or mnem_l.startswith('f') or mnem_l.startswith('v'): return 'Floating Point'
        if 'CRYPTO' in ext_u or 'AES' in ext_u or 'SHA' in ext_u: return 'Cryptography'
        if 'ATOMIC' in ext_u or mnem_l.startswith('ldax') or mnem_l.startswith('stlx'): return 'Atomics & Lock'
        if 'SYSTEM' in ext_u or mnem_l in ['svc', 'hvc', 'smc', 'mrs', 'msr', 'sys']: return 'System & Exception'
        if 'MTE' in ext_u: return 'Memory Tagging (MTE)'
        if 'PAC' in ext_u: return 'Pointer Auth (PAC)'
        if mnem_l.startswith('b') or mnem_l.startswith('cbn') or mnem_l.startswith('tb'): return 'Branch & Control'
        if mnem_l.startswith('ld') or mnem_l.startswith('st'): return 'Load & Store'
        
        return 'Base Instruction'

    # --- RISC-V Categories ---
    # Priority checks based on Extension field or Mnemonic
    if 'Pseudo' in ext: return 'Pseudo-Instructions'
    if 'Compressed' in ext or mnemonic.startswith('C.'): return 'Compressed (16-bit)'
    if 'Vector' in ext or mnemonic.startswith('V'): return 'Vector Operations'
    if 'Crypto' in ext or 'Zk' in ext: return 'Cryptography (Scalar)'
    if 'Float' in ext or 'Double' in ext or mnemonic.startswith('F'): return 'Floating Point'
    if 'Atomic' in ext or mnemonic.startswith('AMO') or mnemonic.startswith('LR.') or mnemonic.startswith('SC.'): return 'Atomics'
    if 'BitManip' in ext: return 'Bit Manipulation'
    if 'Privileged' in ext or 'System' in ext or mnemonic in ['CSRRW', 'MRET', 'WFI', 'URET', 'SRET']: return 'System & Privileged'
    if 'RV64' in ext or mnemonic.endswith('W') or mnemonic in ['LD', 'SD', 'LWU']: return '64-bit Extensions'
    if 'M' in ext or mnemonic in ['MUL', 'DIV', 'REM']: return 'Math Extensions (M)'
    
    return 'Base Integer'

def generate_site(master_db):
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    
    mnemonic_to_url = {}
    search_index = []
    all_pages = []

    # 1. First Pass: Build Index, Unique URLs & Slugs
    for arch, insts in master_db.items():
        slug_counts = {}
        for inst in insts:
            base_slug = inst['mnemonic'].lower().replace(' ', '_').replace('.', '_')
            if base_slug in slug_counts:
                slug_counts[base_slug] += 1
                unique_slug = f"{base_slug}_{slug_counts[base_slug]}"
            else:
                slug_counts[base_slug] = 0
                unique_slug = base_slug
            
            inst['slug'] = unique_slug
            inst['rel_url'] = f"{arch.lower()}/{unique_slug}/"
            mnemonic_to_url[inst['mnemonic']] = f"../../{inst['rel_url']}"
            
            search_index.append({
                "label": f"{inst['mnemonic']} ({arch})",
                "url": inst['rel_url'],
                "summary": inst['summary'],
                "arch": arch
            })
            all_pages.append(inst['rel_url'])

    linkify = create_linkifier(mnemonic_to_url)

    # 2. Write Search Index
    with open(os.path.join(OUTPUT_DIR, 'search.json'), 'w') as f:
        json.dump(search_index, f)

    # 3. Setup Templates
    try:
        template_detail = env.get_template('instruction_detail.html')
        template_summary = env.get_template('arch_summary.html')
        template_index = env.get_template('index.html')
        template_table = env.get_template('opcode_table.html')
    except Exception as e:
        print(f"Error loading templates: {e}")
        return

    # 4. Generate Main Index
    arch_counts = {arch: len(insts) for arch, insts in master_db.items()}
    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w') as f:
        f.write(template_index.render(architectures=list(master_db.keys()), counts=arch_counts, root="."))

    # 5. Generate Architecture & Detail Pages
    for arch, instructions in master_db.items():
        grouped_insts = {}
        sorted_insts = sorted(instructions, key=lambda x: x['mnemonic'])
       
        for inst in sorted_insts:
            if 'encoding' not in inst: inst['encoding'] = {}
            raw_pattern = inst['encoding'].get('binary_pattern') or inst['encoding'].get('pattern')
            if 'operands' not in inst: inst['operands'] = []

            # Visual Encoding
            inst['encoding']['visual_parts'] = []
            if raw_pattern:
                inst['encoding']['binary_pattern'] = raw_pattern 
                raw_parts = parse_encoding(raw_pattern)
                for p in raw_parts:
                    clean_name = p.split('[')[0].strip()
                    inst['encoding']['visual_parts'].append({'raw': p, 'clean': clean_name})

            # --- LINKS & TEXT ---
            # FIX: Escape syntax to prevent browser from hiding <Operands>
            if 'syntax' in inst:
                inst['syntax'] = html.escape(inst['syntax'])

            inst['linked_summary'] = linkify(inst.get('summary', ''))
            inst['linked_pseudocode'] = linkify(inst.get('pseudocode', ''))

            # Categorize
            cat = get_instruction_category(inst)
            if cat not in grouped_insts: grouped_insts[cat] = []
            grouped_insts[cat].append(inst)        

        # Sort groups alphabetically
        sorted_groups = {k: grouped_insts[k] for k in sorted(grouped_insts.keys()) if k in grouped_insts}

        # ARCHITECTURE LANDING PAGE
        arch_dir = os.path.join(OUTPUT_DIR, arch.lower())
        os.makedirs(arch_dir, exist_ok=True)
        with open(os.path.join(arch_dir, 'index.html'), 'w') as f:
            f.write(template_summary.render(arch=arch, instructions=sorted_insts, root=".."))
            
        # OPCODE TABLE
        table_dir = os.path.join(arch_dir, 'table')
        os.makedirs(table_dir, exist_ok=True)
        with open(os.path.join(table_dir, 'index.html'), 'w') as f:
            f.write(template_table.render(arch=arch, instructions=sorted_insts, root="../.."))

        # INSTRUCTION DETAIL PAGES
        for inst in instructions:
            inst_dir = os.path.join(arch_dir, inst['slug'])
            os.makedirs(inst_dir, exist_ok=True)
            with open(os.path.join(inst_dir, 'index.html'), 'w') as f:
                f.write(template_detail.render(
                    instruction=inst,
                    sidebar_groups=sorted_groups,
                    current_page=inst['mnemonic'],
                    root="../.."
                ))
    
    # Save Master DB
    for arch, insts in master_db.items():
        with open(os.path.join(DB_DIR, f"{arch}.json"), 'w') as f:
            # Wrap list in "instructions" key to match input format
            json.dump({"instructions": insts}, f, indent=2)

    print(f"🚀 Website generation complete! Output in '{OUTPUT_DIR}'")

if __name__ == "__main__":
    db = load_data()
    generate_site(db)
