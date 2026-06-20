# QUICK START - USE OLLAMA WITH PROJECT DNA

## 🚀 **START HERE (3 Steps)**

### Step 1: Start Ollama on Network (Terminal 1)
```bash
# Mac/Linux:
OLLAMA_HOST=0.0.0.0:11434 ollama serve

# Windows PowerShell:
$env:OLLAMA_HOST="0.0.0.0:11434"
ollama serve
```

**Result:** Ollama accessible on `http://localhost:11434`

---

### Step 2: Update Project DNA Config

Edit `Backend/.env`:
```env
OLLAMA_API_URL=http://localhost:11434
```

Edit `Backend/chat/views.py` (line ~40):
```python
# Change FROM:
from chat.agent import generate_agent_response

# Change TO:
from chat.agent_ollama import generate_agent_response
```

---

### Step 3: Start Project DNA (Terminal 2)
```bash
cd Backend
python manage.py runserver
```

**Done!** Go to http://localhost:8000

---

## ✅ **VERIFY IT WORKS**

```bash
# Test 1: Ollama running
curl http://localhost:11434/api/tags

# Test 2: Project DNA working
# Sign in to http://localhost:8000
# Connect GitHub repo
# Click "Run Bug Hunt" ✅
```

---

## 🌐 **SHARE WITH OTHERS**

### Get Your IP Address

**Mac/Linux:**
```bash
ifconfig | grep "inet "
```

**Windows:**
```bash
ipconfig | findstr "IPv4"
```

**Result:** Something like `192.168.1.100`

### Share With Others

Tell them:
```
Ollama Server: 192.168.1.100:11434
Project DNA: http://192.168.1.100:8000

(Replace 192.168.1.100 with YOUR IP)
```

### They Can Use Like This

```python
import requests

# Use YOUR laptop's Ollama
response = requests.post(
    "http://192.168.1.100:11434/api/generate",
    json={
        "model": "llama2",
        "prompt": "Hello!",
        "stream": False
    }
)
print(response.json()['response'])
```

---

## 📋 **FULL SETUP IN ONE COMMAND**

### Mac/Linux:
```bash
# Terminal 1: Start Ollama
OLLAMA_HOST=0.0.0.0:11434 ollama serve &

# Terminal 2: Start Project DNA
cd Backend
echo "OLLAMA_API_URL=http://localhost:11434" >> .env
sed -i 's/from chat.agent import/from chat.agent_ollama import/g' chat/views.py
python manage.py runserver
```

### Windows PowerShell:
```bash
# Terminal 1: Start Ollama
$env:OLLAMA_HOST="0.0.0.0:11434"
ollama serve

# Terminal 2: Start Project DNA
cd Backend
Add-Content .env "OLLAMA_API_URL=http://localhost:11434"
# Edit chat/views.py manually, change import
python manage.py runserver
```

---

## 🎯 **WHAT YOU GET**

✅ **Completely FREE AI**
- No paid plans
- No quotas
- No API keys

✅ **Your Laptop = AI Server**
- Others can use your Ollama
- Your data stays private
- Works offline

✅ **Project DNA Features Work**
- Chat about code
- Bug hunting
- Auto-fix suggestions
- PR creation
- File editing

---

## 🔍 **CHECK STATUS**

### Is Ollama Running?
```bash
curl http://localhost:11434/api/tags
# Should show: {"models":[...]}
```

### Is Backend Running?
```bash
curl http://localhost:8000/api/auth/me
# Should show response (may be 401 if not logged in)
```

### Is Everything Connected?
```
1. Go to: http://localhost:8000
2. Sign in
3. Connect GitHub repo
4. See analysis working ✅
```

---

## 🆘 **QUICK FIXES**

**Problem: "Connection refused"**
```bash
# Ollama not running
# Start it: OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

**Problem: "Timeout or very slow"**
```bash
# Model too big, use smaller one
# Edit .env: OLLAMA_MODEL=orca-mini
```

**Problem: "Others can't connect"**
```bash
# Make sure using correct IP
# Test: curl http://YOUR_IP:11434/api/tags
```

**Problem: "Project DNA shows error"**
```bash
# Check .env has: OLLAMA_API_URL=http://localhost:11434
# Restart backend
```

---

## 🚀 **YOU'RE READY!**

Your Project DNA with Ollama is:
- ✅ Completely FREE
- ✅ AI on your laptop
- ✅ Shareable with others
- ✅ Works offline
- ✅ No limits

**Start now and enjoy unlimited free AI!** 🎉
