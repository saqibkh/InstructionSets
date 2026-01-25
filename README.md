# InstructionSets Database

A static website generator that builds a searchable, comprehensive database of CPU Instruction Set Architectures (ISA).

This project transforms raw JSON data definitions into a fast, navigable static website hosted on GitHub Pages. It currently serves as a reference for **RISC-V** and **PowerISA** (including v3.1, VLE, and Embedded/SPE extensions).

## 📊 Current Database Status

The database currently includes coverage for the following architectures and extensions:

### **PowerISA (v3.1 & Embedded)**
* **Base & Integer:** Core 64-bit/32-bit instructions, Rotates, Logical, Traps.
* **Floating Point:** Scalar Double/Single, Quad-Precision (IEEE 754), and Decimal Floating Point.
* **Vector (SIMD):** VMX (AltiVec), VSX (Vector-Scalar), and MMA (Matrix Math Assist) for AI.
* **Embedded & Legacy:** Signal Processing Engine (SPE), Variable Length Encoding (VLE) for Automotive, and 4xx MAC instructions.
* **System:** Supervisor, Hypervisor, Cache Management, and External PID.
* **Crypto:** Hardware AES, SHA, and Elliptic Curve acceleration.

### **RISC-V**
* **Base:** RV32I / RV64I.
* **Extensions:** M (Multiply), A (Atomic), F/D (Float/Double), C (Compressed).
* **Vector:** RVV 1.0 Vector operations.
* **Crypto:** Scalar Cryptography extensions.

---

## 📂 Project Structure

* **`build_site.py`**: The main Python generator script. It parses inputs, links cross-references, and outputs HTML.
* **`input/`**: JSON source files defining the instructions (e.g., `PowerISA_VLE.json`, `RISCV_Vector.json`).
* **`templates/`**: Jinja2 HTML templates (`index.html`, `instruction_detail.html`).
* **`static/`**: CSS and JavaScript assets.
* **`docs/`**: The build output directory (configured for GitHub Pages).

---

## 🚀 Getting Started

### 1. Prerequisites

You need **Python 3.6+** installed. You also need the `jinja2` library for templating.

```bash
pip install jinja2




