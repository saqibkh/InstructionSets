import json
import os

DB_DIR = 'db'
TARGET_ARCH = 'ARMv8-A'
TARGET_MNEMONIC = 'adc'

def debug_instruction():
    filepath = os.path.join(DB_DIR, f"{TARGET_ARCH}.json")
    
    if not os.path.exists(filepath):
        print(f"❌ Could not find {filepath}")
        return

    with open(filepath, 'r') as f:
        data = json.load(f)
        
    found = False
    for inst in data:
        if inst.get('mnemonic', '').lower() == TARGET_MNEMONIC:
            found = True
            print(f"\n🔍 Checking '{TARGET_MNEMONIC}' variant:")
            
            # 1. Check Operands
            ops = inst.get('operands')
            if ops and len(ops) > 0:
                print(f"   ✅ Operands found: {len(ops)} items")
                print(f"      Example: {ops[0]}")
            else:
                print(f"   ❌ Operands MISSING or EMPTY! (Value: {ops})")

            # 2. Check Encoding/Binary Pattern
            encoding = inst.get('encoding', {})
            pattern = encoding.get('binary_pattern')
            if pattern:
                print(f"   ✅ Binary Pattern found: '{pattern}'")
            else:
                print(f"   ❌ Binary Pattern MISSING in encoding dict! Keys found: {list(encoding.keys())}")

            # 3. Check Visual Parts (Generated)
            # Note: This checks the DB file, which might not have visual_parts if build_site.py didn't save them back yet.
            # But the build script generates them in-memory.
            
    if not found:
        print(f"❌ No instruction named '{TARGET_MNEMONIC}' found in {TARGET_ARCH}.json")

if __name__ == "__main__":
    debug_instruction()
