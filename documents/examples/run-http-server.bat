@echo off
echo Starting Postal Codes MCP Server in HTTP/SSE mode...
cd /d "%~dp0\.."
.venv\Scripts\python.exe main.py --transport sse
pause
