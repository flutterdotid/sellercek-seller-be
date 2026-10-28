@echo off
TITLE SellerCek Seller Backend (Port 8008)
COLOR 0B
cd /d "%~dp0"
echo Starting SellerCek Seller Backend on http://localhost:8008 ...

:: Cek virtual environment lokal, buat jika belum ada
if not exist ".venv" (
    echo Membuat .venv dan menginstal dependensi...
    py -3.11 -m venv .venv 2>nul || python -m venv .venv
    call .venv\Scripts\activate.bat
    python -m pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

python -m uvicorn app.main:app --host 0.0.0.0 --port 8008 --reload
pause
