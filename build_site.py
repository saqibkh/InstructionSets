import json
import os
import shutil
from jinja2 import Environment, FileSystemLoader

# --- CONFIGURATION ---
INPUT_DIR = 'input'
DB_DIR = 'db'
OUTPUT_DIR = 'docs'
TEMPLATE_DIR = 'templates'

os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_and_merge_data():
    master_db = {} 
    # 1. Load existing DB
    for filename in os.listdir(DB_DIR):
        if filename.endswith('.json'):
            arch_name = filename.replace('.json', '')
            with open(os.path.join(DB_DIR, filename), 'r') as f:
                master_db[arch_name] = json.load(f)

    # 2. Process new inputs
    if os.path.exists(INPUT_DIR):
        for filename in os.listdir(INPUT_DIR):
            if filename.endswith('.json'):
                filepath = os.path.join(INPUT_DIR, filename)
                with open(filepath, 'r') as f:
                    new_data = json.load(f)
                    for inst in new_data.get('instructions', []):
                        arch = inst.get('architecture', 'Unknown')
                        if arch not in master_db: master_db[arch] = []
                        exists = any(i['mnemonic'] == inst['mnemonic'] for i in master_db[arch])
                        if not exists:
                            master_db[arch].append(inst)
                            print(f"Added {inst['mnemonic']} to {arch}")

    # 3. Save DB
    for arch, instructions in master_db.items():
        with open(os.path.join(DB_DIR, f"{arch}.json"), 'w') as f:
            json.dump(instructions, f, indent=2)
    return master_db


def generate_site(master_db):
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    
    # 1. Search Index (Updated for Clean URLs)
    search_index = []
    for arch, insts in master_db.items():
        for inst in insts:
            clean_name = inst['mnemonic'].lower().replace(' ', '_')
            search_index.append({
                "label": f"{inst['mnemonic']} ({arch})",
                # Point to the folder, not the file
                "url": f"{arch.lower()}/{clean_name}/", 
                "summary": inst['summary']
            })
    
    with open(os.path.join(OUTPUT_DIR, 'search.json'), 'w') as f:
        json.dump(search_index, f)

    # 2. Copy Assets (Using your correct logic)
    static_src = 'static'
    static_dest = os.path.join(OUTPUT_DIR, 'static')
    if os.path.exists(static_dest): shutil.rmtree(static_dest)
    if os.path.exists(static_src): shutil.copytree(static_src, static_dest)

    # 3. Generate Pages
    template_detail = env.get_template('instruction_detail.html')
    template_summary = env.get_template('arch_summary.html')
    template_index = env.get_template('index.html')

    # HOMEPAGE: docs/index.html
    arch_counts = {arch: len(insts) for arch, insts in master_db.items()}
    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w') as f:
        f.write(template_index.render(
            architectures=list(master_db.keys()), 
            counts=arch_counts,
            root="." 
        ))

    for arch, instructions in master_db.items():
        sorted_insts = sorted(instructions, key=lambda x: x['mnemonic'])
        
        # Binary Pattern Logic (Your existing logic)
        for inst in instructions:
            if 'encoding' in inst and 'binary_pattern' in inst['encoding']:
                raw_pattern = inst['encoding']['binary_pattern']
                if '|' in raw_pattern:
                    inst['encoding']['visual_parts'] = [p.strip() for p in raw_pattern.split('|')]
                elif '+' in raw_pattern:
                     inst['encoding']['visual_parts'] = [p.strip() for p in raw_pattern.split('+')]
                else:
                    inst['encoding']['visual_parts'] = [p.strip() for p in raw_pattern.split()]

        # ARCH SUMMARY: docs/risc-v/index.html (Clean URL: /risc-v/)
        arch_dir = os.path.join(OUTPUT_DIR, arch.lower())
        os.makedirs(arch_dir, exist_ok=True)
        
        with open(os.path.join(arch_dir, 'index.html'), 'w') as f:
            f.write(template_summary.render(
                arch=arch, 
                instructions=sorted_insts,
                root=".." # One level deep
            ))
        
        # DETAIL PAGES: docs/risc-v/addi/index.html (Clean URL: /risc-v/addi/)
        for inst in instructions:
            safe_name = inst['mnemonic'].lower().replace(' ', '_')
            
            # Create a folder for the instruction
            inst_dir = os.path.join(arch_dir, safe_name)
            os.makedirs(inst_dir, exist_ok=True)
            
            with open(os.path.join(inst_dir, 'index.html'), 'w') as f:
                f.write(template_detail.render(
                    instruction=inst,
                    sidebar_nav=sorted_insts,
                    current_page=inst['mnemonic'],
                    root="../.." # Two levels deep (risc-v/addi)
                ))

    print("Website generation complete using Clean URLs!")

if __name__ == "__main__":
    print("Scanning for new data...")
    db = load_and_merge_data()
    print("Building HTML...")
    generate_site(db)
