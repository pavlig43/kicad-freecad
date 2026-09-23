@echo off
setlocal
where git >nul 2>nul
if errorlevel 1 (
    echo Git is required to update TrueLib.
    exit /b 2
)
pushd "%~dp0"
if errorlevel 1 exit /b 2
git pull --ff-only
if errorlevel 1 (
    popd
    exit /b 1
)
popd
call "%~dp0install.cmd" %*
exit /b %errorlevel%
