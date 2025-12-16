@echo off
echo Building BenssHelpTools Client...

pushd "%~dp0"
cd app
pyinstaller --noconsole --onefile --name "BenssHelpTools" --clean --hidden-import=PySide6 --hidden-import=websockets main.py

if exist "..\BenssHelpTools.exe" del "..\BenssHelpTools.exe"
move dist\BenssHelpTools.exe ..\

echo.
echo Cleaning up build artifacts...
rmdir /s /q build
rmdir /s /q dist
del BenssHelpTools.spec

popd
echo.
echo Build Complete! Executable is in the client folder: BenssHelpTools.exe
pause
