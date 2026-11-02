# Installation & Setup Guide: Offline Ofrenda Keeper

This guide walks you through setting up and running Offline Ofrenda Keeper on your local machine for pure offline execution.

---

## 1. System Prerequisites

### Supported Operating Systems:
- **Windows:** Windows 10 or 11 (64-bit)
- **Linux:** Ubuntu 22.04+, Debian 12+, Fedora 38+, or equivalent
- **macOS:** macOS 12 (Monterey) or later (Apple Silicon or Intel)

### Software Requirements:
- **Python:** Version **3.12** is recommended (3.10–3.12 supported).
- **Git:** Standard git client for repository management.
- **Hardware Minimum:**
  - **CPU:** 4 physical cores (e.g., Intel 8th Gen Core i5+, AMD Ryzen 3000+, Apple Silicon).
  - **RAM:** **8 GB minimum** (16 GB recommended).
  - **Disk Space:** 4 GB free SSD space for PyTorch libraries and cached neural model weights.

> [!WARNING]
> **Cloud 512 MB Free-Tier Advisory:**  
> Free-tier cloud instances with 512 MB RAM (e.g. Render Free, Fly.io Free) **cannot** run the neural voice recreation pipeline. When PyTorch and the neural models allocate memory during conversion (~1.4 GB peak), the host kernel immediately terminates the container with `SIGKILL (OOM / exit code 137)`. Cloud hosting requires at least **2 GB to 4 GB RAM**.

---

## 2. Windows Installation (PowerShell)

### Step 1: Clone the Repository
Open Windows PowerShell and run:
```powershell
git clone https://github.com/your-username/ofrenda-keeper.git
cd ofrenda-keeper
```

### Step 2: Create Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(If PowerShell blocks script execution, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`)*

### Step 3: Install PyTorch (CPU) and Application Dependencies
Install CPU-only PyTorch first to prevent downloading 3+ GB of unnecessary CUDA packages:
```powershell
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

### Step 4: Pre-Cache Neural Model Weights (One-Time Step with Internet)
Run the automated pre-caching script to download Whisper, Kokoro-82M, and OpenVoice V2 weights into your local Hugging Face cache:
```powershell
.\scripts\fetch_models.ps1
```

### Step 5: Start the Application (Pure Offline Mode)
You can now disconnect your Wi-Fi or enable Airplane Mode:
```powershell
$env:HF_HUB_OFFLINE = "1"
.\scripts\run_production.bat
```
By default, the server binds to **`127.0.0.1:8000` (loopback only)**. Open your web browser to:
**http://127.0.0.1:8000**

*(Optional: To explicitly expose the server across your local Wi-Fi, run: `.\scripts\run_production.bat --lan`. Note that LAN mode has no authentication).*

---

## 3. Linux / macOS Installation

### Step 1: Clone and Set Up Virtual Environment
```bash
git clone https://github.com/your-username/ofrenda-keeper.git
cd ofrenda-keeper
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

### Step 3: Pre-Cache Models
```bash
bash scripts/fetch_models.sh
```

### Step 4: Launch the Server
```bash
export HF_HUB_OFFLINE=1
bash scripts/run_production.sh
```
Visit **http://127.0.0.1:8000** in your browser.

---

## 4. Optional: Setting Up Local Ollama (AI Remembrance Writer)

If you wish to use a local LLM for writing AI remembrances (in addition to the built-in procedural templates):
1. Install Ollama from [https://ollama.com](https://ollama.com).
2. Pull the default lightweight model:
   ```bash
   ollama pull llama3.2:3b
   ```
3. Start the Ollama daemon: `ollama serve`.

*Note: If Ollama is not installed or running, Offline Ofrenda Keeper automatically falls back to culturally respectful deterministic templates in Spanish and English in 0.002 seconds without any application errors.*

---

## 5. Verifying Offline Compliance

Run the automated offline compliance check:
```bash
python scripts/check_offline.py
```
This script recursively audits all templates, styles, JavaScript, and live HTML renders to certify that exactly 0 external CDN links or remote URLs exist.

---

## 6. Troubleshooting

### Port 8000 Already in Use
If another application is using port 8000, specify a different port:
```powershell
$env:PORT = "8080"
.\scripts\run_production.bat
```

### Audio Recording Not Working in Browser
Web browsers require secure contexts or `localhost` to access the microphone. Ensure you are visiting `http://127.0.0.1:8000` or `http://localhost:8000`. If connecting over LAN (`--lan`), modern browsers (Chrome/Firefox/Safari) require HTTPS to enable microphone access.

