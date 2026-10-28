@echo off
setlocal
set "PROJECT_ROOT=%~dp0..\.."
if not defined CUK_ROBOTICS_PYTHON set "CUK_ROBOTICS_PYTHON=C:\miniforge3\envs\cuk-robotics\python.exe"
if not exist "%CUK_ROBOTICS_PYTHON%" (
    echo Set CUK_ROBOTICS_PYTHON to the Python executable in your robotics environment.
    exit /b 1
)
cd /d "%PROJECT_ROOT%"
if not exist "configs\local\powder_train_5070ti\train_config.json" (
    echo Local powder training configuration is missing.
    exit /b 1
)
set "HF_DATASETS_CACHE=%CD%\outputs\inference_matcha_w6_preflight\dataset_cache"
set "HF_HUB_OFFLINE=1"
set "TRANSFORMERS_OFFLINE=1"
"%CUK_ROBOTICS_PYTHON%" -m lerobot.scripts.lerobot_train --config_path=configs/local/powder_train_5070ti/train_config.json %*
exit /b %ERRORLEVEL%
