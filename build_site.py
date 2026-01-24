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
    
    # 1. Search Index
    search_index = []
    for arch, insts in master_db.items():
        for inst in insts:
            search_index.append({
                "label": f"{inst['mnemonic']} ({arch})",
                "url": f"{arch.lower()}/{inst['mnemonic'].lower().replace(' ', '_')}.html",
                "summary": inst['summary']
            })
    
    with open(os.path.join(OUTPUT_DIR, 'search.json'), 'w') as f:
        json.dump(search_index, f)

    # 2. Copy Assets
    # Define source and destination for static files
    static_src = 'static'
    static_dest = os.path.join(OUTPUT_DIR, 'static')

    # Remove old static folder in docs if it exists (clean build)
    if os.path.exists(static_dest):
        shutil.rmtree(static_dest)

    # Copy the entire folder
    if os.path.exists(static_src):
        shutil.copytree(static_src, static_dest)
        print(f"Copied {static_src}/ to {static_dest}/")
    else:
        print("Warning: 'static' folder not found in root.")

    # 3. Generate Pages
    template_detail = env.get_template('instruction_detail.html')
    template_summary = env.get_template('arch_summary.html')
    template_index = env.get_template('index.html')

    # Homepage (Root level)
    arch_counts = {arch: len(insts) for arch, insts in master_db.items()}
    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w') as f:
        f.write(template_index.render(
            architectures=list(master_db.keys()), 
            counts=arch_counts,
            root="." # FIX: Assets are in same folder
        ))

    for arch, instructions in master_db.items():
        sorted_insts = sorted(instructions, key=lambda x: x['mnemonic'])
        
        # FIX: Better Binary Splitting Logic
        for inst in instructions:
            if 'encoding' in inst and 'binary_pattern' in inst['encoding']:
                raw_pattern = inst['encoding']['binary_pattern']
                if '|' in raw_pattern:
                    inst['encoding']['visual_parts'] = [p.strip() for p in raw_pattern.split('|')]
                elif '+' in raw_pattern:
                     inst['encoding']['visual_parts'] = [p.strip() for p in raw_pattern.split('+')]
                else:
                    inst['encoding']['visual_parts'] = [p.strip() for p in raw_pattern.split()]

        # Arch Summary (Root level)
        with open(os.path.join(OUTPUT_DIR, f"{arch.lower()}.html"), 'w') as f:
            f.write(template_summary.render(
                arch=arch, 
                instructions=sorted_insts,
                root="." # FIX: Assets are in same folder
            ))
        
        # Detail Pages (Subfolder level)
        arch_folder = os.path.join(OUTPUT_DIR, arch.lower())
        os.makedirs(arch_folder, exist_ok=True)

        for inst in instructions:
            safe_name = inst['mnemonic'].lower().replace(' ', '_') + ".html"
            with open(os.path.join(arch_folder, safe_name), 'w') as f:
                f.write(template_detail.render(
                    instruction=inst,
                    sidebar_nav=sorted_insts,
                    current_page=inst['mnemonic'],
                    root=".." # FIX: Assets are one level up
                ))

    print("Website generation complete in /docs folder!")

if __name__ == "__main__":
    print("Scanning for new data...")
    db = load_and_merge_data()
    print("Building HTML...")
    generate_site(db)
