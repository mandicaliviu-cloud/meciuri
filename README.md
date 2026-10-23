$ErrorActionPreference = "Stop"

python -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pyinstaller --name "MeciuriAI" --onefile --windowed --noconsole --hidden-import customtkinter main.py
Write-Host "Executable generated in dist/"
