# Project DNA

**AI Code Agent for Every Codebase**

An intelligent, agentic AI platform that connects to your GitHub repositories, analyzes entire codebases, and helps you understand, debug, and improve your code through natural conversation.

## Deployment Links

- **Live Application Frontend**: https://projectdna-aicoding-agent.netlify.app/
- **Live Production Backend**: https://project-dna.onrender.com

## Features

### Core Capabilities
- **Codebase Explorer**: Connect any public GitHub repo and instantly get a complete analysis.
- **AI Chat**: Ask questions about your code and get intelligent, contextual responses.
- **Bug Hunter**: Automated analysis to find potential bugs, security issues, and anti-patterns.
- **Code Review**: AI-powered review of your pull requests with actionable feedback.
- **Code Editor**: Edit files directly in the UI and commit changes to your repo.
- **Dashboard**: Monitor your coding activity, bugs found, PRs reviewed, and more.

### Technical Features
- **Vector-based Code Search**: Uses lightweight semantic similarity matching and self-healing keyword fallback for search index robustness.
- **Static Analysis**: Integrated linting and AST-level code analysis.
- **OAuth Integration**: GitHub and Google Sign-in with account linking.
- **Real-time Chat**: Multi-turn conversations with full conversation history.
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile.
- **Production Ready**: Built with Django REST Framework and React/Vite.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PROJECT DNA PLATFORM                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Frontend (React + Vite)                                    │
│  ├── Landing Page (Marketing)                               │
│  ├── Dashboard (Chat Interface)                             │
│  ├── Repository Manager                                     │
│  └── Code Editor Modal                                      │
│                                                             │
│  Backend (Django REST Framework)                            │
│  ├── Authentication (OAuth + Local)                         │
│  ├── Chat API (LLM Integration)                             │
│  ├── Repository Services (Git Cloning & Analysis)           │
│  ├── Vector Memory (Embeddings & Search)                    │
│  └── AI Features (Bug Hunt, Code Review)                    │
│                                                             │
│  AI Engine (Google Gemini & Groq)                           │
│  ├── Codebase Summarization                                 │
│  ├── Code Analysis                                          │
│  ├── Chat Responses                                         │
│  └── Review Generation                                      │
│                                                             │
│  Database (PostgreSQL)                                      │
│  ├── Users & Authentication                                 │
│  ├── Conversations & Messages                               │
│  ├── Repositories & Metadata                                │
│  └── Code Chunks & Embeddings                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Requirements
- Python 3.10+
- Node.js 16+
- PostgreSQL 12+ (or SQLite for dev)

### 1. Clone and Setup

**Windows:**
```bash
cd Project-DNA
setup.bat
```

**Mac/Linux:**
```bash
cd Project-DNA
chmod +x setup.sh
./setup.sh
```

### 2. Manual Setup (if scripts do not work)

**Backend:**
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

**Frontend:**
```bash
cd Frontend
npm install
npm run build  # for production
# OR
npm run dev    # for development with hot reload
```

### 3. Access the App
- **Backend**: http://localhost:8000
- **Frontend (dev)**: http://localhost:5173 (if running npm run dev)

## API Endpoints

### Auth
- `POST /api/auth/signup` - Register
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Current user
- `GET /auth/google` - Google OAuth
- `GET /auth/github` - GitHub OAuth

### Chat
- `POST /api/chat/send/` - Send message
- `GET /api/chat/conversations/` - List chats
- `POST /api/chat/conversations/` - Create chat
- `GET /api/chat/conversations/{id}/` - Get chat
- `DELETE /api/chat/conversations/{id}/` - Delete chat

### Repos
- `POST /api/repos/connect/` - Connect repo
- `GET /api/repos/` - List connected repos
- `GET /api/repos/github/list` - List your GitHub repos
- `GET /api/repos/file` - Read file
- `POST /api/repos/file` - Write file

### AI
- `POST /api/ai/bug-hunt/` - Analyze for bugs
- `POST /api/ai/code-review/` - Generate review

## Project Structure

```
Project-DNA/
├── Backend/                      # Django REST Framework
│   ├── auth_app/                # Authentication & OAuth
│   │   ├── views.py             # Auth endpoints
│   │   ├── models.py            # User, Repository, etc.
│   │   └── urls.py              # Route definitions
│   ├── chat/                    # Chat & AI Integration
│   │   ├── agent.py             # Gemini/Groq AI agent logic
│   │   ├── views.py             # Chat endpoints
│   │   ├── models.py            # Conversation, Message
│   │   └── static_analysis.py   # Code analysis
│   ├── vectormemory/            # Vector Search
│   │   ├── embeddings.py        # Embeddings helper with fallback
│   │   ├── chunking.py          # Code chunking
│   │   ├── services.py          # Indexing & search
│   │   └── models.py            # CodeChunk model
│   ├── repos/                   # Repository Services
│   │   └── services.py          # Git cloning, analysis
│   ├── backend_project/         # Django config
│   │   ├── settings.py
│   │   └── urls.py
│   ├── manage.py
│   ├── requirements.txt
│   └── .env                     # Environment config
│
├── Frontend/                    # React + Vite
│   ├── src/
│   │   ├── App.jsx              # Main dashboard component
│   │   ├── App.css              # Styles
│   │   └── main.jsx             # React entry point
│   ├── index.html               # Landing page
│   ├── dashboard.html           # Dashboard shell
│   ├── vite.config.js
│   ├── package.json
│   └── dist/                    # Built output
│
├── DEPLOYMENT.md                # Full deployment guide
├── setup.sh                     # Unix setup script
├── setup.bat                    # Windows setup script
└── README.md                    # This file
```

## Environment Configuration

Create a `.env` file in the Backend folder:

```env
# Server
PORT=8000
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173

# Security
SESSION_SECRET=your-secret-key

# Database
DB_NAME=projectdna
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# AI
GEMINI_API_KEY=your-gemini-key
GROQ_API_KEY=your-groq-key

# OAuth
GOOGLE_CLIENT_ID=your-google-id
GOOGLE_CLIENT_SECRET=your-google-secret
GITHUB_CLIENT_ID=your-github-id
GITHUB_CLIENT_SECRET=your-github-secret
```

## Usage Example

1. **Sign In**: Create an account or use OAuth.
2. **Connect Repo**: Paste a GitHub URL or select from a linked account.
3. **Chat**: Ask "What does this repo do?"
4. **Analysis**: Request a bug hunt or code review.
5. **Edit**: View a file in the tree to suggest fixes, apply changes, and commit.

## Security

- CORS configured for localhost and production hosts.
- CSRF protection enabled.
- Session security configured.
- Passwords hashed with Django.
- No API keys in the frontend.
- For production: Update DEBUG, ALLOWED_HOSTS, SSL.

See DEPLOYMENT.md for the production security checklist.

## Tech Stack

### Backend
- **Framework**: Django 5.0 + Django REST Framework
- **Database**: PostgreSQL (development: SQLite)
- **AI/ML**: Google Gemini API, Groq API, sentence-transformers
- **Auth**: OAuth2 (Google, GitHub), Django sessions
- **Analysis**: Static analysis, AST parsing

### Frontend
- **Framework**: React 18
- **Build**: Vite 5
- **CSS**: Custom (no framework)
- **HTTP**: Fetch API

### Infrastructure
- **Deployment**: Docker-ready, works on any WSGI host
- **Vector Search**: In-memory with NumPy (scalable to Redis) and keyword fallback for low-RAM hosts

## Database Schema

### Key Models
- **User**: Django auth + profile (OAuth IDs, GitHub token)
- **Repository**: Connected repos with analysis results
- **Conversation**: Chat sessions (linked to repos)
- **Message**: Individual chat messages
- **CodeChunk**: Indexed code for vector search

## Deployment

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r Backend/requirements.txt
RUN cd Frontend && npm install && npm run build
EXPOSE 8000
CMD ["python", "Backend/manage.py", "runserver", "0.0.0.0:8000"]
```

### Platforms
- **Heroku**: Ready with Procfile
- **AWS/GCP**: Use VM setup or container services
- **Railway/Render**: Connect GitHub repo directly
- **VPS**: Use Gunicorn + Nginx

See DEPLOYMENT.md for detailed platform guides.

## Development Workflow

```bash
# Terminal 1: Backend
cd Backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python manage.py runserver

# Terminal 2: Frontend
cd Frontend
npm run dev
```

Frontend hot reloads at http://localhost:5173 and proxies API to the backend.

## Known Limitations

- Vector search falls back to keyword-based term-frequency ranking on memory-constrained servers (e.g. Render free tier).
- Chat context limited to last 10 messages.
- Polling-based chat.

## Next Steps / Future Features

- Real GitHub write access (file editing + commits)
- WebSocket for real-time chat
- Redis for vector storage scaling
- Async job queue for long analyses
- Team collaboration features
- IDE plugin (VS Code, JetBrains)
- Self-hosted model support

## Troubleshooting

### Backend will not start
```bash
# Check Python version
python --version  # Should be 3.10+

# Check dependencies
pip install -r requirements.txt

# Check database
python manage.py migrate

# Check logs
python manage.py runserver
```

### Frontend build fails
```bash
# Clear cache
rm -rf node_modules dist package-lock.json
npm install
npm run build
```

### Cannot connect to database
- Ensure PostgreSQL is running.
- Check DB credentials in .env.
- Or use SQLite: Update settings.py DATABASES.

### AI responses are generic
- Check GEMINI_API_KEY and GROQ_API_KEY are valid.
- Ensure repo has source code files.
- Verify indexing completed (status = "ready").

See DEPLOYMENT.md for more troubleshooting.

## Resources

- **Django Docs**: https://docs.djangoproject.com/
- **React Docs**: https://react.dev/
- **Gemini API**: https://ai.google.dev/
- **Groq API**: https://groq.com/

## Support

- Check DEPLOYMENT.md for detailed setup.
- Review API endpoint documentation.
- Check environment variables in .env.
- Verify database connectivity.

---

**Project DNA** - Understand any codebase, autonomously.

Built using Django, React, and Gemini/Groq AI.
