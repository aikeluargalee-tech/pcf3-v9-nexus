@echo off
echo ===================================================
echo   NEXUS TERMINAL -- MANUAL CLOUD TELEGRAM DISPATCH
echo ===================================================
echo Triggering GitHub Actions cloud collector...
gh workflow run collector.yml --repo aikeluargalee-tech/pcf3-v9-nexus
if %ERRORLEVEL% EQU 0 goto :ok
goto :fallback

:ok
echo.
echo [SUCCESS] Cloud run triggered!
echo Check your Telegram (@PCF3_Nexus_bot) in approximately 40 seconds.
goto :done

:fallback
echo.
echo [FALLBACK] Triggering direct local transmission...
python scripts\send_telegram_master_packet.py --force

:done
echo.
pause
