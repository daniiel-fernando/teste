@echo off
REM ========================================
REM Script de Desinstalação - Cliente de Notificações Jotanunes
REM Versão 2.1.0
REM ========================================

echo.
echo ========================================
echo  Desinstalação - Cliente Jotanunes
echo  Versão 2.1.0
echo ========================================
echo.

REM Verifica privilégios de administrador
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Executando com privilégios de administrador
) else (
    echo [ERRO] Este script requer privilégios de administrador
    echo Por favor, execute como administrador
    pause
    exit /b 1
)

set "INSTALL_DIR=C:\Program Files\Jotanunes\NotificationClient"
set "SERVICE_NAME=JotanunesNotifications"

echo [INFO] Parando e removendo serviço...
sc stop "%SERVICE_NAME%" >nul 2>&1
sc delete "%SERVICE_NAME%" >nul 2>&1

echo [INFO] Finalizando processos...
taskkill /F /IM "JotanunesNotificationClient.exe" >nul 2>&1
taskkill /F /IM "client_agent.exe" >nul 2>&1

echo [INFO] Removendo inicialização automática...
reg delete "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "JotanunesNotifications" /f >nul 2>&1

echo [INFO] Removendo regra de firewall...
netsh advfirewall firewall delete rule name="Jotanunes Notifications" >nul 2>&1

echo [INFO] Removendo arquivos...
if exist "%INSTALL_DIR%" (
    rmdir /S /Q "%INSTALL_DIR%" >nul 2>&1
    echo [OK] Diretório de instalação removido
)

echo [INFO] Removendo atalhos...
del "C:\Users\Public\Desktop\Jotanunes Notifications.lnk" >nul 2>&1

echo.
echo ========================================
echo  DESINSTALAÇÃO CONCLUÍDA!
echo ========================================
echo.
echo O Cliente de Notificações Jotanunes foi removido completamente.
echo.

pause
exit /b 0

