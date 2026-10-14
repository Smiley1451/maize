@echo off
setlocal
title MAIZE AI ASSISTANT
set "PYTHONPATH=D:\MAIZE_AI_ML_DIGITALIZATION_PROJECT_FINAL\MAIZE_AI_ML_DIGITALIZATION_PROJECT\MAIZE_PHASE21_AI_RESEARCH_ASSISTANT_DROP_IN_V2;D:\MAIZE_AI_ML_DIGITALIZATION_PROJECT_FINAL\MAIZE_AI_ML_DIGITALIZATION_PROJECT"
set "LOKY_MAX_CPU_COUNT=4"
set "PYTHONUTF8=1"
cd /d "D:\MAIZE_AI_ML_DIGITALIZATION_PROJECT_FINAL\MAIZE_AI_ML_DIGITALIZATION_PROJECT"
echo ============================================================
echo MAIZE AI ASSISTANT
echo ============================================================
echo.
echo Starting interactive AI assistant...
echo.
"C:\Users\smile\AppData\Local\Microsoft\WindowsApps\python.exe" -u "D:\MAIZE_AI_ML_DIGITALIZATION_PROJECT_FINAL\MAIZE_AI_ML_DIGITALIZATION_PROJECT\MAIZE_PHASE21_AI_RESEARCH_ASSISTANT_DROP_IN_V2\scripts\run_chat.py"
echo.
echo ============================================================
echo AI assistant process ended.
echo ============================================================
pause
