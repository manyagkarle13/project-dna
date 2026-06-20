# Setup Ollama for Project DNA and Share with Others

## Step-by-Step Guide

### Part 1: Local Setup (Your Computer)

1. **Make sure Ollama is running on network**
```bash
# Start Ollama with network access:
OLLAMA_HOST=0.0.0.0:11434 ollama serve

# Or on Windows PowerShell:
$env:OLLAMA_HOST="0.0.0.0:11434"
ollama serve
```

2. **Find your computer's IP address**
```bash
# Mac/Linux:
ifconfig | grep "inet "

# Windows:
ipconfig | findstr "IPv4"

# Result: Something like 192.168.1.100
```

3. **Test Ollama is accessible**
```bash
curl http://localhost:11434/api/tags
# Should show models
```

4. **Update Project DNA Backend**

Edit `Backend/.env`:
```env
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

5. **Switch to Ollama Agent**

Edit `Backend/chat/views.py`:
```python
# Change this line (around line 40):
from chat.agent_ollama import generate_agent_response
```

6. **Restart Backend**
```bash
cd Backend
python manage.py runserver
```

7. **Test Project DNA**
- Go to http://localhost:8000
- Connect a GitHub repo
- Click "Run Bug Hunt"
- Should work! ✅

---

### Part 2: Share Ollama with Others

1. **Share Your IP Address**

Get from step 2 above. Share with others:
```
My Ollama Server: 192.168.1.100:11434
(Replace with YOUR IP)
```

2. **They Can Access From Command Line**

```bash
# From another computer on your network:
curl -X POST http://192.168.1.100:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama2",
    "prompt": "Hello! What is AI?",
    "stream": false
  }'
```

3. **They Can Use in Their Apps**

```python
import requests

# Connect to YOUR Ollama (your laptop)
ollama_url = "http://192.168.1.100:11434"

response = requests.post(
    f"{ollama_url}/api/generate",
    json={
        "model": "llama2",
        "prompt": "Explain Python",
        "stream": False
    }
)

print(response.json()['response'])
```

---

## 🖥️ **NETWORK SETUP DIAGRAM**

```
Your Laptop (192.168.1.100)
├── Ollama Server (port 11434)
│   └── Model: llama2
│
└── Project DNA Backend (port 8000)
    ├── Uses: http://localhost:11434
    ├── Frontend: http://localhost:5173
    └── Chat Agent: agent_ollama.py

Other Computers on Network
├── Can access: http://192.168.1.100:11434
├── Can use: http://192.168.1.100:8000 (Project DNA)
└── Results in: All use YOUR laptop's Ollama
```

---

## 🔐 **SECURITY & PERMISSIONS**

### Warning
When you expose Ollama on network:
- ✅ Anyone on your WiFi can use it
- ❌ Anyone can make requests to your Ollama
- ❌ Your laptop runs their AI requests
- ❌ Uses your CPU/RAM

### Safe Options
1. **Private Network Only** (recommended)
   - Home WiFi: Safe, only your devices
   - Work WiFi: Check with IT first
   - Public WiFi: DO NOT expose

2. **Authentication** (Advanced)
   - Use firewall to limit access
   - Use VPN for remote access
   - Restrict to specific IPs

### Simple Security
```bash
# Firewall rule (Mac):
sudo pf -f /etc/pf.conf

# Firewall rule (Windows):
New-NetFirewallRule -DisplayName "Ollama" -Direction Inbound -LocalPort 11434 -Action Allow
```

---

## 📊 **OLLAMA MODELS AVAILABLE**

You can use different models with Ollama:

```bash
# List installed models:
ollama list

# Download more models:
ollama pull llama2         # 4GB - Good quality
ollama pull neural-chat    # 5GB - Chat focused
ollama pull mistral        # 15GB - More capable
ollama pull orca-mini      # 3GB - Smallest
```

### Change Model in Project DNA

Edit `Backend/.env`:
```env
OLLAMA_MODEL=neural-chat
# or
OLLAMA_MODEL=mistral
# or
OLLAMA_MODEL=llama2
```

Then restart backend.

---

## 🧪 **TESTING COMMANDS**

### Test 1: Ollama is Running
```bash
curl http://localhost:11434/api/tags
```

### Test 2: Generate Text
```bash
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama2",
    "prompt": "Say hello",
    "stream": false
  }'
```

### Test 3: Others Can Access
```bash
# From another computer:
curl http://192.168.1.100:11434/api/tags
# Should show your models
```

### Test 4: Project DNA Works
```bash
# Sign in to http://localhost:8000
# Connect GitHub repo
# Click "Run Bug Hunt"
# Should analyze code ✅
```

---

## ⚡ **PERFORMANCE TIPS**

### Fast Response
```bash
# Use smaller model:
OLLAMA_MODEL=orca-mini

# This is faster but less accurate
```

### Better Quality
```bash
# Use better model:
OLLAMA_MODEL=mistral

# This is slower but smarter
```

### Speed Up
```bash
# Limit other programs
# Use WiFi (not Bluetooth)
# Close browser tabs
# Disable VPN
```

---

## 🆘 **TROUBLESHOOTING**

### "Connection refused"
```bash
# Ollama not running
# Start it:
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

### "Timeout / Very slow"
```bash
# Model too big
# Switch to smaller:
OLLAMA_MODEL=orca-mini

# Or increase timeout in code
```

### "Others can't access"
```bash
# Check firewall allows port 11434
# Check IP address is correct
# Test: ping 192.168.1.100
```

### "Project DNA shows error"
```bash
# Check OLLAMA_API_URL in .env
# Should be: http://localhost:11434
# Restart backend after changing
```

---

## 🎯 **QUICK START COMMAND**

```bash
# Run this ONE command to start everything:

# Mac/Linux:
OLLAMA_HOST=0.0.0.0:11434 ollama serve &
sleep 2
cd Backend
python manage.py runserver

# Windows PowerShell:
$env:OLLAMA_HOST="0.0.0.0:11434"
ollama serve
# In new terminal:
cd Backend
python manage.py runserver
```

---

## ✅ **VERIFICATION CHECKLIST**

- [ ] Ollama running: `curl http://localhost:11434/api/tags`
- [ ] Backend running: `python manage.py runserver`
- [ ] Frontend accessible: http://localhost:8000
- [ ] Can sign in: Successfully sign in
- [ ] Can connect repo: Connect GitHub repo works
- [ ] Can run bug hunt: Works and analyzes code
- [ ] Others can access: `curl http://YOUR_IP:11434/api/tags`
- [ ] Others can use Project DNA: `http://YOUR_IP:8000`

All checkmarks = Fully working! ✅

---

## 🚀 **SUMMARY**

Your Project DNA with Ollama:
- ✅ Completely FREE
- ✅ AI runs on your laptop
- ✅ Others can use your Ollama
- ✅ Works offline
- ✅ No quotas ever
- ✅ No API keys needed

**Ready to go!** 🎉
