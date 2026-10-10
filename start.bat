@echo off
rem Run the pipeline and restart it whenever it exits (crash, watchdog exit
rem code 3, or a stuck loop). Use this instead of running manage.py by hand.
cd /d %~dp0
:loop
echo [%date% %time%] starting manage.py
Scripts\python.exe manage.py
echo [%date% %time%] manage.py exited with code %ERRORLEVEL%; restarting in 20s (Ctrl+C to stop)
timeout /t 20 /nobreak >nul
goto loop
