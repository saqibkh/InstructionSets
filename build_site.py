import json
import os
import shutil
from jinja2 import Environment, FileSystemLoader

# --- CONFIGURATION ---
INPUT_DIR = 'input'
DB_DIR = 'db'
OUTPUT_DIR = 'docs'
TEMPLATE_DIR = 'templates'

# Ensure directories exist
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- STEP 1: LOAD & MERGE DATA ---
def load_and_merge_data():
    master_db = {} # Key: Architecture, Value: List of instructions

    # 1. Load existing DB files
    for filename in os.listdir(DB_DIR):
        if filename.endswith('.json'):
            arch_name = filename.replace('.json', '')
            with open(os.path.join(DB_DIR, filename), 'r') as f:
                master_db[arch_name] = json.load(f)

    # Copy JS
    if os.path.exists('search.js'):
        shutil.copy('search.js', os.path.join(OUTPUT_DIR, 'search.js'))

    # 2. Process new inputs
    if os.path.exists(INPUT_DIR):
        for filename in os.listdir(INPUT_DIR):
            if filename.endswith('.json'):
                filepath = os.path.join(INPUT_DIR, filename)
                with open(filepath, 'r') as f:
                    new_data = json.load(f)
                    
                    # Assuming input is a list of instructions
                    for inst in new_data.get('instructions', []):
                        arch = inst.get('architecture', 'Unknown')
                        if arch not in master_db:
                            master_db[arch] = []
                        
                        # Check for duplicates (simple check by mnemonic)
                        exists = any(i['mnemonic'] == inst['mnemonic'] for i in master_db[arch])
                        if not exists:
                            master_db[arch].append(inst)
                            print(f"Added {inst['mnemonic']} to {arch}")

    # 3. Save updated DB back to files
    for arch, instructions in master_db.items():
        with open(os.path.join(DB_DIR, f"{arch}.json"), 'w') as f:
            json.dump(instructions, f, indent=2)
            
    return master_db

# --- STEP 2: GENERATE WEBSITE ---
def generate_site(master_db):
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    
    # 1. Generate Search Index
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

    # 2. Copy CSS (Fix: Copy from ROOT to DOCS)
    # Make sure 'style.css' exists in the same folder as this script!
    if os.path.exists('style.css'):
        shutil.copy('style.css', os.path.join(OUTPUT_DIR, 'style.css'))
    else:
        print("Warning: style.css not found in root directory.")

    # 3. Generate Architecture Pages
    template_detail = env.get_template('instruction_detail.html')
    template_summary = env.get_template('arch_summary.html')

    for arch, instructions in master_db.items():
        # Sort instructions for the sidebar
        sorted_insts = sorted(instructions, key=lambda x: x['mnemonic'])
        
        # Summary Page
        with open(os.path.join(OUTPUT_DIR, f"{arch.lower()}.html"), 'w') as f:
            f.write(template_summary.render(
                arch=arch, 
                instructions=sorted_insts
            ))
        
        # Detail Pages
        arch_folder = os.path.join(OUTPUT_DIR, arch.lower())
        os.makedirs(arch_folder, exist_ok=True)

        for inst in instructions:
            safe_name = inst['mnemonic'].lower().replace(' ', '_') + ".html"
            
            with open(os.path.join(arch_folder, safe_name), 'w') as f:
                f.write(template_detail.render(
                    instruction=inst,
                    sidebar_nav=sorted_insts,
                    current_page=inst['mnemonic']
                ))

    # 4. Generate Homepage
    template_index = env.get_template('index.html')
    arch_counts = {arch: len(insts) for arch, insts in master_db.items()}
    
    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w') as f:
        f.write(template_index.render(
            architectures=list(master_db.keys()), 
            counts=arch_counts
        ))

    print("Website generation complete in /docs folder!")

# --- MAIN ---
if __name__ == "__main__":
    print("Scanning for new data...")
    db = load_and_merge_data()
    print("Building HTML...")
    generate_site(db)
