# Patheon

**Patheon** is a static website generator that builds a fast, searchable, and comprehensive reference database for CPU Instruction Set Architectures (ISA).

Designed for performance and offline accessibility, Patheon transforms raw JSON definitions into a static HTML site. It currently serves as a unified reference for **x86 (Intel/AMD)**, **ARMv8/ARMv9**, **RISC-V**, and **PowerISA**.

## 🚀 Features

* **Multi-Architecture Support:** Unified interface for x86, ARM, RISC-V, and PowerISA.
* **Visual Encoding:** Automatically generates bit-field diagrams from instruction patterns.
* **Smart Cross-Linking:** The build engine (`build_site.py`) scans summaries and pseudocode to automatically hyperlink related instructions (e.g., mentioning `VADD` in a summary links to the `VADD` page).
* **Instant Search:** Client-side, JavaScript-based search index for zero-latency lookups.
* **Static & Portable:** No backend database required. The entire site is pre-rendered HTML/CSS, suitable for GitHub Pages or local documentation.

---

## 📊 Database Coverage

The database currently includes coverage for the following architectures and extensions:

### **x86 / x64 (Intel & AMD)**
* **General Purpose:** Legacy x86, x64, and System instructions.
* **SIMD Extensions:** MMX, SSE (1-4.2), and AVX / AVX2.
* **High Performance:** AVX-512 (Foundation, VL, BW, DQ) and **AMX** (Advanced Matrix Extensions) for AI workloads.
* **Security & Specialized:** AES-NI, SHA, TSX (Transactional Synchronization), and Key Locker.

### **ARM (v8-A & v9-A)**
* **AArch64 & AArch32:** Base instructions and system control.
* **Advanced SIMD:** NEON and floating-point operations.
* **Scalable Vectors:** **SVE** (Scalable Vector Extension) and **SME** (Scalable Matrix Extension) / SME2.
* **Security:** PAC (Pointer Authentication), BTI, and Crypto extensions (SM3/SM4, SHA3).

### **RISC-V**
* **Base ISA:** RV32I / RV64I.
* **Standard Extensions:** M (Multiply), A (Atomic), F/D/Q (Floating Point), C (Compressed).
* **Modern Extensions:** **V (Vector)**, **H (Hypervisor)**, and Bit Manipulation (Zb*).
* **Crypto:** Scalar (Zk*) and Vector Crypto standards.

### **PowerISA (v3.1 & Embedded)**
* **Base & Integer:** Core 64-bit instructions and Traps.
* **Vector (SIMD):** VMX (AltiVec), VSX, and **MMA** (Matrix Math Assist).
* **Embedded:** VLE (Variable Length Encoding) and SPE (Signal Processing Engine).
* **System:** Supervisor, Hypervisor, and External PID management.

---

## 🛠️ Building the Site

Patheon is built in Python using Jinja2.

### Prerequisites
* Python 3.8+
* Dependencies: `jinja2`, `markdown` (if used for descriptions)

### Build Command
To regenerate the entire site from the `input/` JSON files:

```bash
python build_site.py

## 📝 Adding New Instructions

Data is stored in the `input/` directory as JSON "batches". To add a new instruction, create or append to a JSON file using the following schema:

```json
{
  "mnemonic": "vadd.vv",
  "architecture": "RISC-V",
  "full_name": "Vector Integer Add",
  "summary": "Adds vector register elements.",
  "syntax": "vadd.vv vd, vs2, vs1, vm",
  "encoding": {
    "format": "Vector",
    "hex_opcode": "0x0...",
    "length": "32",
    "binary_pattern": "000000 | 11111 | 00000 | 000 | 11111 | 1010111"
  },
  "extension": "V",
  "pseudocode": "vd[i] = vs2[i] + vs1[i]"
}
