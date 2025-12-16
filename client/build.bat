@echo off
echo [1/3] Cleaning previous builds...
rmdir /s /q build
rmdir /s /q dist
del /q *.spec

echo [2/3] Building Client App with PyInstaller...
pyinstaller --noconfirm --onedir --windowed --name "BenssHelpTools" --add-data "settings.json;." app/main.py

echo [3/3] Build Complete!
echo Output is in dist/BenssHelpTools
pause
