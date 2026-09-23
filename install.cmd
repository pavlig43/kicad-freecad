@echo off
where py >nul 2>nul
if %errorlevel% equ 0 (
    py -3 "%~dp0scripts\install.py" %*
) else (
    python "%~dp0scripts\install.py" %*
)
