# Project DNA - Complete Deployment Guide

## 📋 Project Overview

Project DNA is a fully functional agentic AI coding platform that:
- Connects to GitHub repositories
- Analyzes entire codebases using Gemini AI
- Provides AI chat about code
- Finds bugs and security issues
- Reviews pull requests
- Allows direct code editing with commits

## ✅ Completed Features

### Authentication & User Management
- ✅ Google OAuth login
- ✅ GitHub OAuth login (with account linking)
- ✅ Email/password local authentication
- ✅ User profiles and session management
- ✅ JWT and Django session auth

### Repository Analysis
- ✅ Repository cloning and analysis
- ✅ Tech stack detection
- ✅ File tree building
- ✅ Codebase summarization with Gemini AI
- ✅ Vector memory indexing (sentence-transformers)
- ✅ Semantic code chunk search

### Chat & AI Features
- ✅ Multi-turn conversations
- ✅ Repository-aware context retrieval
- ✅ Bug hunting analysis
- ✅ Code review generation
- ✅ Static analysis integration
- ✅ Conversation history management

### Code Editor
- ✅ File reading from repos
- ✅ File editing with commit support
- ✅ Mock file writing (ready for GitHub API)

### Frontend Dashboard
- ✅ Landing page with hero section
- ✅ Responsive dashboard UI
- ✅ Real-time chat interface
- ✅ Repository connection flow
- ✅ File tree explorer
- ✅ Code editor modal
- ✅ Dashboard stats
- ✅ Mobile-responsive design

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 16+
- PostgreSQL 12+ (or SQLite for development)
- Git

### Step 1: Setup Backend

```bash
cd Backend

# Create and activate virtual environment (if not already done)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
```

### Step 2: Setup Frontend

```bash
cd Frontend

# Install dependencies
npm install

# Build for production (or run dev server)
npm run build  # Creates dist/ folder
# OR for development:
npm run dev    # Starts Vite dev server on http://localhost:5173
```

### Step 3: Start the Application

**Backend (Django)**
```bash
cd Backend
source venv/bin/activate  # Activate virtual environment
python manage.py runserver 0.0.0.0:8000
```

The backend will serve:
- Landing page: `http://localhost:8000/`
- Dashboard: `http://localhost:8000/dashboard.html`
- API endpoints: `http://localhost:8000/api/*`

**Frontend Dev Server (Optional)**
```bash
cd Frontend
npm run dev  # For development with hot reload
```

## 🔧 Configuration

### Environment Variables

Create/update `.env` in the Backend directory:

```env
# Server Configuration
PORT=8000
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173

# Django Security
SESSION_SECRET=your-secret-key-here

# Database (PostgreSQL recommended for production)
DB_NAME=projectdna
DB_USER=postgres
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

# Gemini API
GEMINI_API_KEY=your-gemini-api-key

# OAuth Credentials (optional - uses mock auth if not set)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

### Optional: Using SQLite for Development

Update `Backend/backend_project/settings.py` DATABASES section:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
```

## 📁 Project Structure

```
Project-DNA/
├── Backend/
│   ├── auth_app/         # Authentication & OAuth
│   ├── chat/             # Chat & AI agent
│   ├── vectormemory/     # Vector embeddings & search
│   ├── repos/            # Repository services
│   ├── manage.py
│   ├── requirements.txt
│   └── .env
├── Frontend/
│   ├── src/              # React components
│   ├── dist/             # Built output (after npm run build)
│   ├── index.html        # Landing page
│   ├── dashboard.html    # Dashboard entry point
│   ├── package.json
│   └── vite.config.js
└── DEPLOYMENT.md         # This file
```

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - Login with email/password
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Get current user
- `GET /auth/google` - Google OAuth redirect
- `GET /auth/github` - GitHub OAuth redirect

### Chat
- `GET /api/chat/conversations/` - List user's conversations
- `POST /api/chat/conversations/` - Create new conversation
- `GET /api/chat/conversations/{id}/` - Get conversation detail
- `POST /api/chat/send/` - Send message
- `DELETE /api/chat/conversations/{id}/` - Delete conversation

### Repositories
- `GET /api/repos/` - List connected repos
- `GET /api/repos/github/list` - List GitHub repos (if linked)
- `POST /api/repos/connect/` - Connect a repository
- `GET /api/repos/file?repo_id=X&file_path=Y` - Read file
- `POST /api/repos/file` - Write file

### AI Features
- `POST /api/ai/bug-hunt/` - Run bug analysis
- `POST /api/ai/code-review/` - Generate code review

### Dashboard
- `GET /api/dashboard/stats` - Get user stats

## 🧪 Testing the Application

### Test User Registration/Login
1. Open http://localhost:8000/
2. Click "Get started" or "Sign in"
3. Choose authentication method:
   - **Email/Password**: Enter credentials to sign up or login
   - **Google**: Click "Continue with Google"
   - **GitHub**: Click "Continue with GitHub"

### Test Repository Connection
1. After login, go to dashboard
2. Click "Connect a repo" button
3. If GitHub is linked: Select from your repos
4. If not linked: Paste a public repo URL (e.g., `https://github.com/user/repo`)
5. Wait for analysis to complete

### Test Chat
1. Connected repo will appear in the banner
2. Type a question about the code
3. AI will respond with context-aware analysis

### Test Bug Hunt
1. With a repo connected, click "Run Bug Hunt" button
2. System will analyze code for vulnerabilities

### Test Code Review
1. Click "Code Review" button
2. Get AI-generated review of recent changes

## 🐛 Troubleshooting

### Database Connection Error
- Ensure PostgreSQL is running
- Check `.env` database credentials
- Try using SQLite for development (see Configuration)
- Run: `python manage.py migrate`

### Gemini API Errors
- Verify `GEMINI_API_KEY` in `.env`
- Check API key is valid and has sufficient quota
- Ensure internet connection is available

### Frontend Build Issues
- Clear `Frontend/dist` and `node_modules`
- Run `npm install` again
- Run `npm run build`

### OAuth Not Working
- If credentials missing, app falls back to mock auth
- For real OAuth, ensure:
  - Credentials are correctly set in `.env`
  - Callback URLs are registered in provider settings
  - `BACKEND_URL` matches what's registered

### Vector Search Returns No Results
- Repo must have at least 50 characters of source code
- Indexing happens automatically during repo connection
- Check if repo status is "ready" (not "processing" or "failed")

## 📦 Building for Production

### Backend
```bash
cd Backend
# Collect static files
python manage.py collectstatic --noinput

# Use a production WSGI server (gunicorn)
pip install gunicorn
gunicorn backend_project.wsgi:application --bind 0.0.0.0:8000
```

### Frontend
```bash
cd Frontend
# Build for production (already done in Quick Start)
npm run build

# Serve dist folder with backend
# Backend will serve from /static/ path
```

### Docker (Optional)
Create `Dockerfile` for containerization:
```dockerfile
FROM python:3.10
WORKDIR /app
COPY Backend/requirements.txt .
RUN pip install -r requirements.txt
COPY Backend /app/
COPY Frontend/dist /app/static/
CMD ["gunicorn", "backend_project.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## 🔐 Security Considerations for Production

- [ ] Set `DEBUG = False` in Django settings
- [ ] Update `SECRET_KEY` to a strong random value
- [ ] Use HTTPS (configure SSL/TLS)
- [ ] Set `ALLOWED_HOSTS` to specific domains
- [ ] Use environment variables for all secrets
- [ ] Enable CSRF protection properly
- [ ] Configure CORS for specific origins only
- [ ] Use strong database passwords
- [ ] Enable rate limiting on API endpoints
- [ ] Regular security updates for dependencies

## 📝 Environment-Specific Configurations

### Development
```env
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE=SQLite (optional)
```

### Production
```env
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DATABASE=PostgreSQL (recommended)
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

## 🚢 Deployment Platforms

### Heroku
1. Create Procfile: `web: gunicorn backend_project.wsgi`
2. Set environment variables in Heroku dashboard
3. Deploy: `git push heroku main`

### AWS / DigitalOcean / GCP
1. Setup VM with Python and PostgreSQL
2. Clone repository
3. Follow "Building for Production" section
4. Use systemd service for Django
5. Setup Nginx as reverse proxy
6. Configure SSL with Let's Encrypt

### Railway / Render / Fly.io
1. Connect GitHub repository
2. Set environment variables
3. Configure build command: `pip install -r requirements.txt && npm run build`
4. Configure start command: `gunicorn backend_project.wsgi:application`

## 📚 API Documentation

### Chat API Example

**Send a message:**
```bash
curl -X POST http://localhost:8000/api/chat/send/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What does this codebase do?",
    "conversation_id": 1,
    "repo_id": 1
  }'
```

**List conversations:**
```bash
curl http://localhost:8000/api/chat/conversations/
```

### Repository API Example

**Connect a repo:**
```bash
curl -X POST http://localhost:8000/api/repos/connect/ \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/user/repo",
    "full_name": "user/repo",
    "default_branch": "main"
  }'
```

## 🛠️ Development Workflow

### Local Development

```bash
# Terminal 1: Backend
cd Backend
source venv/bin/activate
python manage.py runserver

# Terminal 2: Frontend (for hot reload)
cd Frontend
npm run dev
```

Then access:
- Backend API: http://localhost:8000
- Frontend: http://localhost:5173
- Vite proxies API calls to backend

### Making Changes

**Backend Changes:**
- Edit Python files
- Django auto-reloads on save
- API changes test with curl or frontend

**Frontend Changes:**
- Edit React/JSX files
- Vite hot-reloads automatically
- See changes in real-time

## 📊 Database Schema

Key models:
- `User` - Django auth user
- `UserProfile` - Extended user data (OAuth IDs, tokens)
- `Repository` - Connected repositories
- `Conversation` - Chat conversations
- `Message` - Chat messages
- `CodeChunk` - Indexed code for vector search

## 🎓 Learning Resources

- Django: https://docs.djangoproject.com/
- React: https://react.dev/
- Vite: https://vitejs.dev/
- Gemini API: https://ai.google.dev/
- Vector Search: https://www.sbert.net/

## 📞 Support

For issues or questions:
1. Check the Troubleshooting section
2. Review API endpoint docs above
3. Check Django/React error messages
4. Verify .env configuration

## 🎉 Next Steps

After deployment:
1. Test all core features
2. Configure domain/SSL
3. Set up monitoring
4. Configure backups
5. Document your deployment
6. Consider adding:
   - WebSocket for real-time chat
   - Async job queue for long analyses
   - Caching layer (Redis)
   - CI/CD pipeline

## 📄 License

[Add your license here]

---

**Project DNA - AI Code Agent for Every Codebase**
Build date: 2026-06-19
Last updated: 2026-06-19
