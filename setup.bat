@echo off
REM Project DNA Setup Script for Windows

echo.
echo 🧬 Project DNA - Complete Setup Script (Windows)
echo ================================================
echo.

REM Check if we're in the right directory
if not exist "Backend\manage.py" (
    echo ❌ Error: Please run this script from the Project-DNA root directory
    exit /b 1
)

echo [Step 1] Setting up Backend
echo.

cd Backend

REM Check if venv exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate.bat

echo Installing backend dependencies...
pip install -r requirements.txt -q

echo Running database migrations...
python manage.py migrate --noinput

echo ✓ Backend setup complete
echo.

cd ..

echo [Step 2] Setting up Frontend
echo.

cd Frontend

echo Installing frontend dependencies...
call npm install --silent

echo Building frontend...
call npm run build

echo ✓ Frontend setup complete
echo.

cd ..

echo.
echo ================================================
echo ✨ Setup Complete!
echo.
echo Next steps:
echo.
echo 1. Backend (Django):
echo    cd Backend
echo    venv\Scripts\activate
echo    python manage.py runserver
echo.
echo 2. Frontend (Vite dev server - optional):
echo    cd Frontend
echo    npm run dev
echo.
echo 3. Access the application:
echo    http://localhost:8000  (Backend + compiled frontend)
echo    http://localhost:5173  (Frontend dev server, if running)
echo.
echo 📝 For detailed configuration, see DEPLOYMENT.md
echo.
pause
