@echo off
echo ======================================================================
echo   AI-Powered Financial PDF Data Extraction System - Setup Script
echo ======================================================================
echo.

REM Check Python
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+
    exit /b 1
) else (
    python --version
    echo ✓ Python found
)

REM Check Node.js
echo Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found. Please install Node.js 16+
    exit /b 1
) else (
    node --version
    echo ✓ Node.js found
)

REM Check MongoDB
echo Checking MongoDB installation...
mongod --version >nul 2>&1
if errorlevel 1 (
    echo ⚠ MongoDB not found locally. You can use MongoDB Atlas instead.
    echo   Visit: https://www.mongodb.com/cloud/atlas
) else (
    mongod --version
    echo ✓ MongoDB found
)

echo.
echo ======================================================================
echo   Step 1: Creating Project Structure
echo ======================================================================
echo.

mkdir data\sample_pdfs 2>nul
mkdir extracted 2>nul
mkdir api\routes 2>nul
mkdir services 2>nul
mkdir config 2>nul
mkdir models 2>nul
mkdir tests 2>nul
mkdir utils 2>nul
echo ✓ Project directories created

echo.
echo ======================================================================
echo   Step 2: Python Environment Setup
echo ======================================================================
echo.

if not exist venv (
    python -m venv venv
    echo ✓ Python virtual environment created
) else (
    echo ✓ Python virtual environment already exists
)

echo Activating virtual environment...
call venv\Scripts\activate.bat
if exist requirements.txt (
    pip install --upgrade pip
    pip install -r requirements.txt
    echo ✓ Python dependencies installed
) else (
    echo ⚠ requirements.txt not found, skipping Python dependencies installation
)

echo Downloading spaCy language model...
python -m spacy download en_core_web_sm
echo ✓ spaCy model downloaded

echo.
echo ======================================================================
echo   Step 3: Node.js Setup
echo ======================================================================
echo.

if exist package.json (
    echo Installing Node.js dependencies...
    npm install --silent
    echo ✓ Node.js dependencies installed
) else (
    echo ⚠ package.json not found, skipping npm install
)

echo.
echo ======================================================================
echo   Step 4: Environment Configuration
echo ======================================================================
echo.

if not exist .env (
    echo Creating .env file...
    echo PORT=3000> .env
    echo NODE_ENV=development>> .env
    echo MONGODB_URI=mongodb://localhost:27017/financial_extraction>> .env
    echo ✓ .env file created
) else (
    echo ✓ .env file already exists
)

echo.
echo ======================================================================
echo   Setup Complete! 🎉
echo ======================================================================
echo.
echo Next Steps:
echo 1. Place your PDF bank statements in: data\sample_pdfs\
echo 2. Process PDFs:
echo    python process_pdf.py data\sample_pdfs\your-file.pdf user123
echo    OR process all PDFs:
echo    python process_pdf.py data\sample_pdfs user123 --dir
echo 3. Start the API server:
echo    npm run dev
echo 4. Import transactions to database:
echo    curl -X POST http://localhost:3000/api/transactions/import ^
echo      -H "Content-Type: application/json" ^
echo      -d "{\"filePath\": \"extracted/transactions_user123_*.json\", \"userId\": \"user123\"}"
echo 5. Test the API:
echo    npm test
echo 6. Access API documentation:
echo    http://localhost:3000
echo.
pause
