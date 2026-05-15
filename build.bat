@echo off
echo Building Terminal Config Editor...
pyinstaller build.spec --noconfirm --clean
echo.
echo Build complete! exe 文件在 dist/TerminalConfig.exe
pause
