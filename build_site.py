import os
import json
import shutil
import re
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
    for filename in os.listdir(INPUT_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(INPUT_DIR, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    
                    # Merge into master_db grouped by Architecture
                    for inst in data.get('instructions', []):
                        arch = inst.get('architecture', 'Unknown')
                        
                        # --- NEW: Deduplication Logic ---
                        # Create a unique signature based on key fields
                        # We use Mnemonic + Syntax + Hex Opcode to distinguish variants
                        signature = (
                            inst.get('mnemonic', '').strip(),
                            inst.get('syntax', '').strip(),
                            inst.get('encoding', {}).get('hex_opcode', '').strip()
                        )
                        
                        if signature in seen_hashes:
                            # Skip this instruction if we've already seen an exact match
                            continue
                        
                        seen_hashes.add(signature)
                        # --------------------------------
                        
                        if arch not in master_db:
                            master_db[arch] = []
                        master_db[arch].append(inst)
            except Exception as e:
                print(f"Error reading {filename}: {e}")
                
    return master_db

def parse_encoding(pattern_str):
    """
    Parses encoding strings safely.
    Returns a list of parts or an empty list if input is invalid.
    """
    if not pattern_str or not isinstance(pattern_str, str):
        return []
    
    # Split by '|', strip whitespace, and filter out empty strings
    parts = [p.strip() for p in pattern_str.split('|') if p.strip()]
    return parts

def create_linkifier(mnemonic_to_url):
    """
    Creates a function that auto-links instruction mnemonics in text.
    """
    # Sort by length descending to match longest mnemonics first (e.g., "VADD.VV" before "VADD")
    sorted_keys = sorted(mnemonic_to_url.keys(), key=len, reverse=True)
    
    # Escape for regex
    escaped_keys = [re.escape(k) for k in sorted_keys]
    
    # Create regex pattern: match word boundaries to avoid partial matches
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
        slug_counts = {} # Track mnemonic usage to handle duplicates
        
        for inst in insts:
            # Create base slug
            base_slug = inst['mnemonic'].lower().replace(' ', '_').replace('.', '_')
            
            # Handle Duplicates: Append _1, _2, etc. if needed
            if base_slug in slug_counts:
                slug_counts[base_slug] += 1
                unique_slug = f"{base_slug}_{slug_counts[base_slug]}"
            else:
                slug_counts[base_slug] = 0
                unique_slug = base_slug
            
            # Save these fields to the instruction object for the templates to use
            inst['slug'] = unique_slug
            inst['rel_url'] = f"{arch.lower()}/{unique_slug}/"
            
            # Build search index
            mnemonic_to_url[inst['mnemonic']] = f"../../{inst['rel_url']}"
            search_index.append({
                "label": f"{inst['mnemonic']} ({arch})",
                "url": inst['rel_url'],
                "summary": inst['summary'],
                "arch": arch
            })
            all_pages.append(inst['rel_url'])

    linkify = create_linkifier(mnemonic_to_url)

    # 2. Generate Sitemap.xml
    sitemap_content = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    today = datetime.now().strftime("%Y-%m-%d")
    sitemap_content.append(f"  <url><loc>{SITE_URL}/</loc><lastmod>{today}</lastmod></url>")
    for page in all_pages:
        full_url = f"{SITE_URL}/{page}"
        sitemap_content.append(f"  <url><loc>{full_url}</loc><lastmod>{today}</lastmod></url>")
    sitemap_content.append('</urlset>')
    
    with open(os.path.join(OUTPUT_DIR, 'sitemap.xml'), 'w') as f:
        f.write('\n'.join(sitemap_content))
    print(f"✅ Generated sitemap.xml with {len(all_pages) + 1} URLs")

    # 3. Write Search Index
    with open(os.path.join(OUTPUT_DIR, 'search.json'), 'w') as f:
        json.dump(search_index, f)

    # 4. Setup Templates (THIS WAS MISSING)
    template_detail = env.get_template('instruction_detail.html')
    template_summary = env.get_template('arch_summary.html')
    template_index = env.get_template('index.html')
    template_table = env.get_template('opcode_table.html')

    # 5. Generate robots.txt
    with open(os.path.join(OUTPUT_DIR, 'robots.txt'), 'w') as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml")
    
    # 6. Copy Static Assets & CNAME
    static_src = 'static'
    static_dest = os.path.join(OUTPUT_DIR, 'static')
    if os.path.exists(static_dest): shutil.rmtree(static_dest)
    if os.path.exists(static_src): shutil.copytree(static_src, static_dest)

    if os.path.exists('CNAME'):
        shutil.copy('CNAME', os.path.join(OUTPUT_DIR, 'CNAME'))
        print("✅ Copied CNAME to output directory")

    # 7. Generate Main Index (Landing Page)
    arch_counts = {arch: len(insts) for arch, insts in master_db.items()}
    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w') as f:
        f.write(template_index.render(architectures=list(master_db.keys()), counts=arch_counts, root="."))

    # 8. Generate Architecture & Detail Pages
    for arch, instructions in master_db.items():
        
        # --- Grouping Logic ---
        grouped_insts = {}
        # Sort instructions alphabetically first
        sorted_insts = sorted(instructions, key=lambda x: x['mnemonic'])
       
        for inst in sorted_insts:
            # --- 1. DATA NORMALIZATION (Fix common issues) ---
            
            # Ensure 'encoding' dict exists
            if 'encoding' not in inst: inst['encoding'] = {}
            
            # Fallback: Look for 'pattern' if 'binary_pattern' is missing
            raw_pattern = inst['encoding'].get('binary_pattern') or inst['encoding'].get('pattern')
            
            # Fallback: Ensure 'operands' is a list
            if 'operands' not in inst: inst['operands'] = []

            # --- 2. PROCESS VISUAL ENCODING ---
            inst['encoding']['visual_parts'] = [] # Default to empty
            
            if raw_pattern:
                # Store the normalized pattern back so the template sees it
                inst['encoding']['binary_pattern'] = raw_pattern 
                
                raw_parts = parse_encoding(raw_pattern)
                for p in raw_parts:
                    # Clean up "rs1[4:0]" -> "rs1" for tooltip matching
                    clean_name = p.split('[')[0].strip()
                    inst['encoding']['visual_parts'].append({'raw': p, 'clean': clean_name})
            else:
                # OPTIONAL: Print warning for missing patterns so you can fix JSON later
                print(f"⚠️  Warning: No binary pattern for {inst['mnemonic']} ({arch})")

            # --- 3. LINKS & TEXT ---
            # Add Auto-Links
            inst['linked_summary'] = linkify(inst.get('summary', ''))
            inst['linked_pseudocode'] = linkify(inst.get('pseudocode', ''))

            # Categorize
            cat = get_instruction_category(inst)
            if cat not in grouped_insts: grouped_insts[cat] = []
            grouped_insts[cat].append(inst)        

        # Define Sort Order for Sidebar
        cat_order = [
            'Base Integer', '64-bit Extensions', 'Math Extensions (M)', 
            'Floating Point', 'Atomics', 'Bit Manipulation', 
            'Cryptography (Scalar)', 'Vector Operations', 'Compressed (16-bit)', 
            'System & Privileged', 'Pseudo-Instructions',
            'Load & Store', 'Branch & Control', 'Comparison & CR',
            'Cache Management', 'Vector (VMX/AltiVec)', 
            'Vector-Scalar (VSX)', 'Prefixed (64-bit)'
        ]
        
        # Sort groups
        sorted_groups = {k: grouped_insts[k] for k in cat_order if k in grouped_insts}
        for k in grouped_insts:
            if k not in sorted_groups: sorted_groups[k] = grouped_insts[k]

        # ARCHITECTURE LANDING PAGE
        arch_dir = os.path.join(OUTPUT_DIR, arch.lower())
        os.makedirs(arch_dir, exist_ok=True)
        
        with open(os.path.join(arch_dir, 'index.html'), 'w') as f:
            f.write(template_summary.render(
                arch=arch, 
                instructions=sorted_insts, 
                root=".."
            ))
            
        # GENERATE ARCHITECTURE JSON
        with open(os.path.join(arch_dir, 'instructions.json'), 'w') as f:
            json.dump(instructions, f, indent=2)
       
        # GENERATE OPCODE TABLE
        def get_op_int(inst):
            try:
                op_str = inst.get('encoding', {}).get('hex_opcode', '')
                clean = re.sub(r'[^0-9a-fA-F]', '', op_str)
                return int(clean, 16) if clean else 9999999
            except:
                return 9999999

        sorted_by_opcode = sorted(instructions, key=get_op_int)
        
        table_dir = os.path.join(arch_dir, 'table')
        os.makedirs(table_dir, exist_ok=True)
        with open(os.path.join(table_dir, 'index.html'), 'w') as f:
            f.write(template_table.render(
                arch=arch,
                instructions=sorted_by_opcode,
                root="../.."
            ))
        print(f"   └── Generated pages for {arch}")

        # INSTRUCTION DETAIL PAGES
        for inst in instructions:
            # Use unique slug for folder name
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
            json.dump(insts, f, indent=2)

    print(f"🚀 Website generation complete! Output in '{OUTPUT_DIR}'")

if __name__ == "__main__":
    db = load_data()
    generate_site(db)
