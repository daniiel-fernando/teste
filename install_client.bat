@echo off
REM ========================================
REM Script de Instalação - Cliente de Notificações Jotanunes
REM Versão 2.1.0 - Instalação Robusta
REM ========================================

echo.
echo ========================================
echo  Cliente de Notificações Jotanunes
echo  Versão 2.1.0 - Instalação Automática
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

REM Define diretórios
set "INSTALL_DIR=C:\Program Files\Jotanunes\NotificationClient"
set "TEMP_DIR=%TEMP%\JotanunesInstall"
set "SERVICE_NAME=JotanunesNotifications"

echo.
echo [INFO] Criando diretórios de instalação...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

REM Para o serviço se estiver executando
echo [INFO] Parando serviço existente (se houver)...
sc stop "%SERVICE_NAME%" >nul 2>&1
taskkill /F /IM "JotanunesNotificationClient.exe" >nul 2>&1
taskkill /F /IM "client_agent.exe" >nul 2>&1

REM Copia arquivos
echo [INFO] Copiando arquivos do cliente...
if exist "JotanunesNotificationClient.exe" (
    copy "JotanunesNotificationClient.exe" "%INSTALL_DIR%\" >nul
    echo [OK] Executável copiado
) else if exist "dist\JotanunesNotificationClient.exe" (
    copy "dist\JotanunesNotificationClient.exe" "%INSTALL_DIR%\" >nul
    echo [OK] Executável copiado do diretório dist
) else (
    echo [ERRO] Executável não encontrado
    echo Certifique-se de que JotanunesNotificationClient.exe está no mesmo diretório
    pause
    exit /b 1
)

REM Copia arquivos de configuração se existirem
if exist "jnunes_logo.png" copy "jnunes_logo.png" "%INSTALL_DIR%\" >nul
if exist "LogoVermelha-Branca.png" copy "LogoVermelha-Branca.png" "%INSTALL_DIR%\" >nul
if exist "Logo.JOTA.3.ico" copy "Logo.JOTA.3.ico" "%INSTALL_DIR%\" >nul

REM Configura inicialização automática no registro
echo [INFO] Configurando inicialização automática...
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "JotanunesNotifications" /t REG_SZ /d "\"%INSTALL_DIR%\JotanunesNotificationClient.exe\"" /f >nul
if %errorLevel% == 0 (
    echo [OK] Inicialização automática configurada
) else (
    echo [AVISO] Erro ao configurar inicialização automática
)

REM Configura firewall (permite comunicação)
echo [INFO] Configurando firewall...
netsh advfirewall firewall delete rule name="Jotanunes Notifications" >nul 2>&1
netsh advfirewall firewall add rule name="Jotanunes Notifications" dir=out action=allow program="%INSTALL_DIR%\JotanunesNotificationClient.exe" >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Regra de firewall configurada
) else (
    echo [AVISO] Erro ao configurar firewall
)

REM Cria serviço Windows (opcional)
echo [INFO] Configurando como serviço Windows...
sc create "%SERVICE_NAME%" binPath= "\"%INSTALL_DIR%\JotanunesNotificationClient.exe\"" start= auto DisplayName= "Jotanunes Notification Client" >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Serviço Windows criado
    sc description "%SERVICE_NAME%" "Cliente de notificações corporativas da Jotanunes" >nul
) else (
    echo [AVISO] Erro ao criar serviço (pode já existir)
)

REM Cria atalho na área de trabalho para todos os usuários
echo [INFO] Criando atalho na área de trabalho...
set "DESKTOP_PUBLIC=C:\Users\Public\Desktop"
if exist "%DESKTOP_PUBLIC%" (
    echo [Windows Script Host] > "%TEMP_DIR%\create_shortcut.vbs"
    echo Set oWS = WScript.CreateObject("WScript.Shell") >> "%TEMP_DIR%\create_shortcut.vbs"
    echo sLinkFile = "%DESKTOP_PUBLIC%\Jotanunes Notifications.lnk" >> "%TEMP_DIR%\create_shortcut.vbs"
    echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP_DIR%\create_shortcut.vbs"
    echo oLink.TargetPath = "%INSTALL_DIR%\JotanunesNotificationClient.exe" >> "%TEMP_DIR%\create_shortcut.vbs"
    echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> "%TEMP_DIR%\create_shortcut.vbs"
    echo oLink.Description = "Cliente de Notificações Jotanunes" >> "%TEMP_DIR%\create_shortcut.vbs"
    echo oLink.IconLocation = "%INSTALL_DIR%\Logo.JOTA.3.ico" >> "%TEMP_DIR%\create_shortcut.vbs"
    echo oLink.Save >> "%TEMP_DIR%\create_shortcut.vbs"
    
    cscript //nologo "%TEMP_DIR%\create_shortcut.vbs" >nul 2>&1
    if %errorLevel% == 0 (
        echo [OK] Atalho criado na área de trabalho
    ) else (
        echo [AVISO] Erro ao criar atalho
    )
)

REM Inicia o cliente
echo [INFO] Iniciando cliente de notificações...
start "" "%INSTALL_DIR%\JotanunesNotificationClient.exe"

REM Limpeza
if exist "%TEMP_DIR%" rmdir /S /Q "%TEMP_DIR%" >nul 2>&1

echo.
echo ========================================
echo  INSTALAÇÃO CONCLUÍDA COM SUCESSO!
echo ========================================
echo.
echo O Cliente de Notificações Jotanunes foi instalado em:
echo %INSTALL_DIR%
echo.
echo Configurações aplicadas:
echo - Inicialização automática: SIM
echo - Serviço Windows: SIM
echo - Regra de firewall: SIM
echo - Atalho na área de trabalho: SIM
echo.
echo O cliente foi iniciado automaticamente.
echo Verifique o ícone na bandeja do sistema.
echo.

REM Mostra informações de teste
echo Para testar a instalação:
echo 1. Verifique o ícone na bandeja do sistema
echo 2. Clique com botão direito no ícone para ver o menu
echo 3. Selecione "Status" para verificar a conexão
echo.

pause
exit /b 0

