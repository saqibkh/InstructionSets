import json
import os
import shutil
import re
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# --- CONFIGURATION ---
INPUT_DIR = 'input'
DB_DIR = 'db'
OUTPUT_DIR = 'docs'
TEMPLATE_DIR = 'templates'
SITE_URL = "https://saqibkh.github.io/InstructionSets" 

os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- HELPERS ---
def validate_instruction(inst):
    required = ['mnemonic', 'architecture', 'summary', 'encoding']
    missing = [key for key in required if key not in inst]
    if missing:
        print(f"⚠️  Warning: {inst.get('mnemonic', 'Unknown')} missing keys: {missing}")
        return False
    return True

def parse_encoding(pattern):
    if not pattern: return []
    if '|' in pattern: return [p.strip() for p in pattern.split('|')]
    if '+' in pattern: return [p.strip() for p in pattern.split('+')]
    return [p.strip() for p in pattern.split()]

def create_linkifier(mnemonic_map):
    sorted_keys = sorted(mnemonic_map.keys(), key=len, reverse=True)
    pattern = re.compile(r'\b(' + '|'.join(re.escape(k) for k in sorted_keys) + r')\b')

    def linkify(text):
        if not text: return ""
        def replace(match):
            m = match.group(0)
            return f'<a href="{mnemonic_map[m]}" class="cross-link">{m}</a>'
        return pattern.sub(replace, text)
    return linkify

# --- CORE LOGIC ---
def load_and_merge_data():
    master_db = {} 
    if os.path.exists(DB_DIR):
        for filename in os.listdir(DB_DIR):
            if filename.endswith('.json'):
                arch_name = filename.replace('.json', '')
                with open(os.path.join(DB_DIR, filename), 'r') as f:
                    master_db[arch_name] = json.load(f)

    if os.path.exists(INPUT_DIR):
        for filename in os.listdir(INPUT_DIR):
            if filename.endswith('.json'):
                filepath = os.path.join(INPUT_DIR, filename)
                with open(filepath, 'r') as f:
                    try:
                        new_data = json.load(f)
                        for inst in new_data.get('instructions', []):
                            if not validate_instruction(inst): continue
                            arch = inst.get('architecture', 'Unknown')
                            if arch not in master_db: master_db[arch] = []
                            exists = any(i['mnemonic'] == inst['mnemonic'] for i in master_db[arch])
                            if not exists:
                                master_db[arch].append(inst)
                                print(f"✅ Added {inst['mnemonic']} to {arch}")
                    except json.JSONDecodeError as e:
                        print(f"❌ Error decoding {filename}: {e}")

    for arch, instructions in master_db.items():
        with open(os.path.join(DB_DIR, f"{arch}.json"), 'w') as f:
            json.dump(instructions, f, indent=2)
    return master_db


# --- NEW: Categorization Helper ---
def get_instruction_category(inst):
    ext = inst.get('extension', '')
    mnemonic = inst.get('mnemonic', '')
    
    # Priority checks based on Extension field or Mnemonic
    if 'Pseudo' in ext: return 'Pseudo-Instructions'
    if 'Compressed' in ext or mnemonic.startswith('C.'): return 'Compressed (16-bit)'
    if 'Vector' in ext or mnemonic.startswith('V'): return 'Vector Operations'
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

    # 1. First Pass: Build Index & URLs
    for arch, insts in master_db.items():
        for inst in insts:
            clean_name = inst['mnemonic'].lower().replace(' ', '_')
            clean_name = clean_name.replace('.', '_') # Handle FADD.D -> fadd_d
            rel_url = f"{arch.lower()}/{clean_name}/"
            mnemonic_to_url[inst['mnemonic']] = f"../../{rel_url}"
            
            search_index.append({
                "label": f"{inst['mnemonic']} ({arch})",
                "url": rel_url,
                "summary": inst['summary'],
                "arch": arch
            })
            all_pages.append(rel_url)

    linkify = create_linkifier(mnemonic_to_url)

    # 2. Write Search & Sitemap
    with open(os.path.join(OUTPUT_DIR, 'search.json'), 'w') as f:
        json.dump(search_index, f)

    # (Sitemap code omitted for brevity - keeps existing logic)

    static_src = 'static'
    static_dest = os.path.join(OUTPUT_DIR, 'static')
    if os.path.exists(static_dest): shutil.rmtree(static_dest)
    if os.path.exists(static_src): shutil.copytree(static_src, static_dest)

    template_detail = env.get_template('instruction_detail.html')
    template_summary = env.get_template('arch_summary.html')
    template_index = env.get_template('index.html')

    # 3. Generate Pages
    arch_counts = {arch: len(insts) for arch, insts in master_db.items()}
    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w') as f:
        f.write(template_index.render(architectures=list(master_db.keys()), counts=arch_counts, root="."))

    for arch, instructions in master_db.items():
        # --- NEW: Grouping Logic ---
        grouped_insts = {}
        # Pre-sort all instructions alphabetically first
        sorted_insts = sorted(instructions, key=lambda x: x['mnemonic'])
        
        for inst in sorted_insts:
            # Process encoding/links (Keep existing logic)
            if 'encoding' in inst and 'binary_pattern' in inst['encoding']:
                raw_parts = parse_encoding(inst['encoding']['binary_pattern'])
                inst['encoding']['visual_parts'] = []
                for p in raw_parts:
                    clean_name = p.split('[')[0].strip()
                    inst['encoding']['visual_parts'].append({'raw': p, 'clean': clean_name})
            
            inst['linked_summary'] = linkify(inst['summary'])
            inst['linked_pseudocode'] = linkify(inst.get('pseudocode', ''))

            # Categorize
            cat = get_instruction_category(inst)
            if cat not in grouped_insts: grouped_insts[cat] = []
            grouped_insts[cat].append(inst)

        # Define Custom Sort Order for Categories
        cat_order = [
            'Base Integer', '64-bit Extensions', 'Math Extensions (M)', 
            'Floating Point', 'Atomics', 'Bit Manipulation', 
            'Vector Operations', 'Compressed (16-bit)', 
            'System & Privileged', 'Pseudo-Instructions'
        ]
        # Sort the dictionary by this list
        sorted_groups = {k: grouped_insts[k] for k in cat_order if k in grouped_insts}
        # Add any remaining categories at the end
        for k in grouped_insts:
            if k not in sorted_groups: sorted_groups[k] = grouped_insts[k]

        # ARCH SUMMARY
        arch_dir = os.path.join(OUTPUT_DIR, arch.lower())
        os.makedirs(arch_dir, exist_ok=True)
        with open(os.path.join(arch_dir, 'index.html'), 'w') as f:
            f.write(template_summary.render(
                arch=arch, 
                instructions=sorted_insts, # Keep flat list for table summary
                root=".."
            ))
        
        # DETAIL PAGES
        for inst in instructions:
            safe_name = inst['mnemonic'].lower().replace(' ', '_').replace('.', '_')
            inst_dir = os.path.join(arch_dir, safe_name)
            os.makedirs(inst_dir, exist_ok=True)
            
            with open(os.path.join(inst_dir, 'index.html'), 'w') as f:
                f.write(template_detail.render(
                    instruction=inst,
                    sidebar_groups=sorted_groups, # PASS GROUPS INSTEAD OF LIST
                    current_page=inst['mnemonic'],
                    root="../.."
                ))

    print("🚀 Website generation complete!")

if __name__ == "__main__":
    print("Scanning for new data...")
    db = load_and_merge_data()
    print("Building HTML...")
    generate_site(db)
