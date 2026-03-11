@echo off
echo ==========================================
echo  Djezzy BSS Mobile - APK Builder
echo ==========================================
echo.

REM Check for Java
where java >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Java not found. Please install Android Studio or JDK 17.
    echo Download: https://developer.android.com/studio
    echo After installing, open this script again.
    pause
    exit /b 1
)

REM Check JAVA_HOME
if "%JAVA_HOME%"=="" (
    echo [WARNING] JAVA_HOME not set. Trying to detect...
    for /d %%d in ("C:\Program Files\Android\Android Studio\jbr") do set "JAVA_HOME=%%d"
    if "%JAVA_HOME%"=="" (
        for /d %%d in ("C:\Program Files\Java\jdk*") do set "JAVA_HOME=%%d"
    )
    if "%JAVA_HOME%"=="" (
        echo [ERROR] Could not find JAVA_HOME. Set it manually:
        echo   set JAVA_HOME=C:\Path\To\Your\JDK
        pause
        exit /b 1
    )
    echo [OK] Found JAVA_HOME: %JAVA_HOME%
)

echo.
echo [1/3] Syncing web assets...
cd /d "%~dp0"
call npx cap sync android
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Capacitor sync failed.
    pause
    exit /b 1
)

echo.
echo [2/3] Building debug APK...
cd android
call .\gradlew.bat assembleDebug
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Build failed. Make sure Android SDK is installed.
    pause
    exit /b 1
)

echo.
echo [3/3] Copying APK...
cd /d "%~dp0"
copy "android\app\build\outputs\apk\debug\app-debug.apk" "DjezzyBSS.apk" >nul 2>&1

echo.
echo ==========================================
echo  BUILD SUCCESSFUL!
echo ==========================================
echo.
echo APK file: %~dp0DjezzyBSS.apk
echo.
echo Send this DjezzyBSS.apk file to your  
echo colleagues. They install it on their
echo Android phone and configure the server 
echo IP on first launch.
echo ==========================================
pause
