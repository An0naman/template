@echo off
cd /d "%~dp0"

:: Check if proxy is already running
netstat -ano | findstr ":8080" >nul 2>&1
if %errorlevel% == 0 goto launch

:: Start the proxy server in background
echo Starting Ollama Chat server...
start /B /MIN node ollama-proxy.js >nul 2>&1

:: Wait for it to be ready
timeout /t 2 /nobreak >nul

:launch
:: Open the installed PWA if it exists, otherwise open Chrome
start chrome --app=http://localhost:8080
