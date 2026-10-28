@echo off
setlocal
set "PROJECT_ROOT=%~dp0..\.."
if not defined CUK_ROBOTICS_PYTHON set "CUK_ROBOTICS_PYTHON=C:\miniforge3\envs\cuk-robotics\python.exe"
if not exist "%CUK_ROBOTICS_PYTHON%" (
    echo Set CUK_ROBOTICS_PYTHON to the Python executable in your robotics environment.
    exit /b 1
)
if /I "%~1"=="matcha" (
    set "POLICY_PATH=models/matcha-shaker-w6-261008-01"
) else if /I "%~1"=="tkpota" (
    set "POLICY_PATH=models/smolvla_so101_beverage_multitask"
) else (
    echo Usage: infer_beverage.bat matcha^|tkpota powder^|water [run_robot options]
    exit /b 2
)
if /I "%~2"=="powder" (
    set "DATASET_ROOT=data/lerobot/lmsforai/so101_bimanual_beverage_powder_v1/merged_v1"
    set "TASK=With the left arm, pour powder into the fixed central bowl and return the powder container to its starting position."
) else if /I "%~2"=="water" (
    set "DATASET_ROOT=data/lerobot/lmsforai/so101_bimanual_beverage_water_v1/20261006_202550_457396"
    set "TASK=With the right arm, pick up the beaker, pour water into the fixed central cup, and return the beaker to its starting position."
) else (
    echo Usage: infer_beverage.bat matcha^|tkpota powder^|water [run_robot options]
    exit /b 2
)
cd /d "%PROJECT_ROOT%"
set "HF_HUB_OFFLINE=1"
set "TRANSFORMERS_OFFLINE=1"
"%CUK_ROBOTICS_PYTHON%" scripts/run_robot.py infer --policy-path "%POLICY_PATH%" --dataset-root "%DATASET_ROOT%" --task "%TASK%" --wrist-fourcc MJPG --duration-s 100 --no-target-limit --return-to-initial-position %3 %4 %5 %6 %7 %8 %9
exit /b %ERRORLEVEL%
