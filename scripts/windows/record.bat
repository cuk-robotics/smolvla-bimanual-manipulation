@echo off
setlocal
set "PROJECT_ROOT=%~dp0..\.."
if not defined CUK_ROBOTICS_PYTHON set "CUK_ROBOTICS_PYTHON=C:\miniforge3\envs\cuk-robotics\python.exe"
if not exist "%CUK_ROBOTICS_PYTHON%" (
    echo Set CUK_ROBOTICS_PYTHON to the Python executable in your robotics environment.
    pause
    exit /b 1
)
cd /d "%PROJECT_ROOT%"
"%CUK_ROBOTICS_PYTHON%" "%PROJECT_ROOT%\scripts\run_robot.py" --project-root "%PROJECT_ROOT%" record %*
set "RESULT=%ERRORLEVEL%"
pause
exit /b %RESULT%
