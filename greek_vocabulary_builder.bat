@echo off
setlocal EnableDelayedExpansion

cls
echo ===================================
echo      Greek Vocaburaly Learner
echo ===================================
echo.


set "APP_PATH=C:\Users\oktac\OneDrive\Documents\python codes\greek_vocabulary_builder\app.py"
set "START_PORT=8501"
set "END_PORT=8509"
set "PORT="

REM Check each port from START_PORT to END_PORT
for /L %%P in (%START_PORT%,1,%END_PORT%) do (
    netstat -ano | findstr :%%P >nul
    if errorlevel 1 (
        set "PORT=%%P"
        goto :RUN
    )
)

echo All ports from %START_PORT% to %END_PORT% are busy.
goto :EOF

:RUN
echo Launching Greek Vocaburaly Learner app on port !PORT!
streamlit run "!APP_PATH!" --server.port !PORT!