@echo off
setlocal
set "GRADLE_VERSION=8.11.1"
where gradle >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  gradle %*
  exit /b %ERRORLEVEL%
)
set "GRADLE_USER_HOME=%GRADLE_USER_HOME%"
if "%GRADLE_USER_HOME%"=="" set "GRADLE_USER_HOME=%USERPROFILE%\.gradle"
set "DIST_DIR=%GRADLE_USER_HOME%\wrapper\dists\amitysa-gradle-%GRADLE_VERSION%"
set "GRADLE_HOME=%DIST_DIR%\gradle-%GRADLE_VERSION%"
set "GRADLE_BIN=%GRADLE_HOME%\bin\gradle.bat"
if not exist "%GRADLE_BIN%" (
  if not exist "%DIST_DIR%" mkdir "%DIST_DIR%"
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; Invoke-WebRequest -Uri 'https://services.gradle.org/distributions/gradle-%GRADLE_VERSION%-bin.zip' -OutFile '%DIST_DIR%\gradle.zip'; Expand-Archive -Path '%DIST_DIR%\gradle.zip' -DestinationPath '%DIST_DIR%' -Force; Remove-Item '%DIST_DIR%\gradle.zip'"
  if errorlevel 1 exit /b 1
)
if not exist "%GRADLE_BIN%" (
  echo Gradle bootstrap failed.
  exit /b 1
)
call "%GRADLE_BIN%" %*
exit /b %ERRORLEVEL%
