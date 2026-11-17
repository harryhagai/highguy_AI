@echo off
rem Highguy AI Assistant - double-click this file to start it in CMD.
rem Extra words are passed on, e.g.:  open_highguy_ai.bat swahili
title Highguy AI Assistant
cd /d "%~dp0"
mode con: cols=90 lines=42 >nul 2>&1
chcp 65001 >nul

if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
    goto run
)
where py >nul 2>&1
if %errorlevel%==0 (
    set "PYTHON=py -3"
    goto run
)
set "PYTHON=python"

:run
%PYTHON% src\main.py %*
if errorlevel 1 (
    echo.
    echo Highguy AI stopped with an error. Is Python installed?
    pause
)
