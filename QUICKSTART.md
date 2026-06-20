# ⚡ Project DNA - Quick Start Guide

## 🚀 Get Running in 2 Minutes

### Automatic Setup

**Windows Users:**
```bash
cd Project-DNA
setup.bat
```

**Mac/Linux Users:**
```bash
cd Project-DNA
chmod +x setup.sh
./setup.sh
```

The script will:
1. Create virtual environment
2. Install backend dependencies
3. Run database migrations
4. Install frontend dependencies
5. Build the frontend

### Manual Setup (if scripts don't work)

**Terminal 1 - Backend:**
```bash
cd Backend
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

**Terminal 2 - Frontend (Optional, for development):**
```bash
cd Frontend
npm install
npm run dev  # For hot reload development
```

## 📍 Access the App

- **Main Application**: http://localhost:8000
- **Frontend Dev (optional)**: http://localhost:5173
- **Admin Panel (optional)**: http://localhost:8000/admin

## 🎯 First Steps

1. **Sign In**
   - Click "Get started" on landing page
   - Use email/password, Google, or GitHub

2. **Connect a Repository**
   - Paste a public GitHub URL: `https://github.com/user/repo`
   - OR select from your GitHub repos if linked

3. **Chat with AI**
   - Ask: "What does this repo do?"
   - Ask: "Find bugs in this code"
   - Ask: "Review this code"

4. **Explore Features**
   - Click "Run Bug Hunt" to find vulnerabilities
   - Click "Code Review" for PR analysis
   - Click file to edit in modal

## ⚙️ Configuration

### Essential: Set Gemini API Key

Edit `Backend/.env`:
```env
GEMINI_API_KEY=your-api-key-here
```

Get a free key: https://ai.google.dev/

### Optional: OAuth Setup

For real GitHub/Google login instead of mock:
```env
GOOGLE_CLIENT_ID=your-id
GOOGLE_CLIENT_SECRET=your-secret
GITHUB_CLIENT_ID=your-id
GITHUB_CLIENT_SECRET=your-secret
```

### Optional: Database

For SQLite (development):
- Already configured, works out of box

For PostgreSQL (production):
```env
DB_NAME=projectdna
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
```

## 📁 Project Structure

```
Backend/           → Django API
Frontend/          → React UI
README.md          → Full overview
DEPLOYMENT.md      → How to deploy
COMPLETION.md      → What's included
```

## 🔗 API Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/signup` | POST | Register user |
| `/api/auth/login` | POST | Login |
| `/api/chat/send/` | POST | Send message |
| `/api/repos/connect/` | POST | Connect repo |
| `/api/ai/bug-hunt/` | POST | Find bugs |
| `/api/ai/code-review/` | POST | Review code |

See DEPLOYMENT.md for full API docs.

## 🔧 PR Creation Workflows

### Workflow 1: Auto-Fix Bugs & Create PR

1. Connect a GitHub repository
2. Click **"🔧 Auto-Fix & PR"** button
3. System analyzes code for bugs
4. AI generates fixes automatically
5. **Pull request created** with fixes applied
6. Review and merge on GitHub

**Requirements:**
- GitHub account linked to Project DNA
- Write access to the repository

### Workflow 2: Edit File & Create PR

1. Click a file in the File Tree to open editor
2. Make your changes in the editor modal
3. Click **"Create PR"** button
4. New branch created with your changes
5. **Pull request opened** for review
6. Commit and branch managed automatically

**Requirements:**
- GitHub account linked
- Write access to repository

### Workflow 3: Chat-Driven PR Creation

Ask the AI in chat to fix issues:
- "Fix the SQL injection vulnerability in auth.py"
- "Optimize the database queries"
- "Update deprecated API calls"

The AI can generate fixes and create PRs directly from chat.

## 🆘 Troubleshooting

### "ModuleNotFoundError: No module named 'django'"
```bash
pip install -r requirements.txt
```

### "npm: command not found"
Install Node.js from https://nodejs.org/

### "Cannot find module 'vite'"
```bash
cd Frontend
npm install
```

### "GEMINI_API_KEY not set"
1. Add to `Backend/.env`
2. Restart backend: `python manage.py runserver`

### Port 8000 already in use
```bash
python manage.py runserver 0.0.0.0:8001
```

### "GitHub token not found" when creating PR
1. Click "Connect GitHub for full access" button
2. Authenticate with your GitHub account
3. Authorize Project DNA to access your repositories
4. Try creating PR again

### PR creation fails with "Permission denied"
- Verify you have write access to the repository
- Check that the repository isn't archived
- Ensure OAuth scopes include `repo` access

## 📚 Documentation

- **README.md** - Complete project overview
- **DEPLOYMENT.md** - Detailed deployment guide (50+ sections)
- **COMPLETION.md** - What's been built
- **This file** - Quick start

## 🚀 Deploy to Production

### Option 1: Docker (Easiest)
```bash
docker build -t projectdna .
docker run -p 8000:8000 projectdna
```

### Option 2: Heroku
```bash
git push heroku main
```

### Option 3: Railway/Render
Connect GitHub repo and they handle it.

See DEPLOYMENT.md for detailed platform guides.

## ✨ Features Ready to Use

✅ Sign up / Sign in  
✅ Connect GitHub repos  
✅ Chat with AI about code  
✅ Run bug analysis  
✅ **Auto-fix bugs & create PRs** ← NEW!
✅ Generate code reviews  
✅ Edit files and create PRs ← NEW!
✅ View conversation history  
✅ Dashboard with stats  

## 🎓 Learn More

- **Full setup guide**: See README.md
- **Deployment options**: See DEPLOYMENT.md
- **What's built**: See COMPLETION.md
- **API endpoints**: See DEPLOYMENT.md (API Documentation section)

---

**That's it! You're ready to go. Start the backend and visit http://localhost:8000** 🎉
