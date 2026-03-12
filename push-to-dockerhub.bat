@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM Configuration variables (modify these)
set "DOCKER_USERNAME=your-dockerhub-username"
set "DOCKER_IMAGE_NAME=image-analysis"
set "DOCKER_TAG=latest"

REM Full image name
set "FULL_IMAGE_NAME=%DOCKER_USERNAME%/%DOCKER_IMAGE_NAME%:%DOCKER_TAG%"

:menu
cls
echo ==========================================
echo   Docker Image Push Tool (Windows)
echo ==========================================
echo.
echo Current Config:
echo   Docker Hub User: %DOCKER_USERNAME%
echo   Image Name: %DOCKER_IMAGE_NAME%
echo   Image Tag: %DOCKER_TAG%
echo   Full Image: %FULL_IMAGE_NAME%
echo.
echo Please select:
echo   1) Configure parameters
echo   2) Build image
echo   3) Login to Docker Hub
echo   4) Push image
echo   5) Full process (build+login+push)
echo   6) View image info
echo   7) Cleanup old images
echo   0) Exit
echo.
set /p choice="Please enter option [0-7]: "

if "%choice%"=="1" goto configure_params
if "%choice%"=="2" goto build_image
if "%choice%"=="3" goto login_dockerhub
if "%choice%"=="4" goto push_image
if "%choice%"=="5" goto full_process
if "%choice%"=="6" goto show_image_info
if "%choice%"=="7" goto cleanup_old_images
if "%choice%"=="0" goto exit
goto invalid_option

:configure_params
cls
echo ==========================================
echo   Configure Docker Hub Parameters
echo ==========================================
echo.

set /p input_username="Docker Hub Username [%DOCKER_USERNAME%]: "
if not "!input_username!"=="" set "DOCKER_USERNAME=!input_username!"

set /p input_image_name="Image Name [%DOCKER_IMAGE_NAME%]: "
if not "!input_image_name!"=="" set "DOCKER_IMAGE_NAME=!input_image_name!"

set /p input_tag="Image Tag [%DOCKER_TAG%]: "
if not "!input_tag!"=="" set "DOCKER_TAG=!input_tag!"

set "FULL_IMAGE_NAME=%DOCKER_USERNAME%/%DOCKER_IMAGE_NAME%:%DOCKER_TAG%"

echo.
echo [SUCCESS] Configuration updated!
echo.
echo Image Name: %FULL_IMAGE_NAME%
echo.
pause
goto menu

:build_image
cls
echo [INFO] Building Docker image...
echo.
echo [INFO] Image name: %FULL_IMAGE_NAME%
echo.

if not exist "Dockerfile" (
    echo [ERROR] Dockerfile not found, please run in project root
    pause
    goto menu
)

docker build -t %FULL_IMAGE_NAME% .

if %errorlevel% equ 0 (
    echo [SUCCESS] Image built successfully!
    echo.
    docker images | findstr %DOCKER_IMAGE_NAME%
) else (
    echo [ERROR] Image build failed
)

echo.
pause
goto menu

:login_dockerhub
cls
echo [INFO] Login to Docker Hub...
echo.

docker login

if %errorlevel% equ 0 (
    echo [SUCCESS] Docker Hub login successful
) else (
    echo [ERROR] Docker Hub login failed
)

echo.
pause
goto menu

:push_image
cls
echo [INFO] Pushing image to Docker Hub...
echo.
echo [INFO] Image: %FULL_IMAGE_NAME%
echo.

docker push %FULL_IMAGE_NAME%

if %errorlevel% equ 0 (
    echo [SUCCESS] Image pushed successfully!
    echo.
    echo ==========================================
    echo  Now you can search this image in Baota panel
    echo ==========================================
    echo.
    echo Search keyword: %DOCKER_USERNAME%/%DOCKER_IMAGE_NAME%
    echo.
    echo Or pull directly in Baota Docker management:
    echo %FULL_IMAGE_NAME%
    echo.
    echo ==========================================
) else (
    echo [ERROR] Image push failed
    echo.
    echo Please check:
    echo 1. If logged in to Docker Hub
    echo 2. If image name is correct
    echo 3. If network connection is normal
)

echo.
pause
goto menu

:full_process
cls
echo [INFO] Starting full process...
echo.

REM 1. Build image
echo [INFO] Step 1/3: Building image...
call :build_image
if %errorlevel% neq 0 goto menu

REM 2. Login
echo.
echo [INFO] Step 2/3: Login to Docker Hub...
call :login_dockerhub
if %errorlevel% neq 0 goto menu

REM 3. Push
echo.
echo [INFO] Step 3/3: Pushing image...
call :push_image

echo.
echo [SUCCESS] Full process completed!
pause
goto menu

:show_image_info
cls
echo [INFO] Local images:
echo.
docker images | findstr %DOCKER_IMAGE_NAME%
if %errorlevel% neq 0 (
    echo [WARN] Image not found
)

echo.
pause
goto menu

:cleanup_old_images
cls
echo [INFO] Cleaning up old Docker images...
echo.

echo Removing dangling images...
docker image prune -f

echo.
echo Removing unused images...
docker image prune -a -f

echo.
echo [SUCCESS] Cleanup completed
echo.
pause
goto menu

:invalid_option
cls
echo [ERROR] Invalid option
echo.
pause
goto menu

:exit
cls
echo [INFO] Exiting...
timeout /t 1 >nul
exit /b 0
