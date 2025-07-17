@echo off
REM ========================================
REM Script de Compilação - Cliente de Notificações Jotanunes
REM Versão 2.1.0
REM ========================================

echo.
echo ========================================
echo  Compilação - Cliente Jotanunes
echo  Versão 2.1.0
echo ========================================
echo.

REM Verifica se Python está instalado
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERRO] Python não encontrado
    echo Por favor, instale Python 3.7 ou superior
    pause
    exit /b 1
)

echo [OK] Python encontrado

REM Verifica se PyInstaller está instalado
python -m PyInstaller --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [INFO] PyInstaller não encontrado, instalando...
    python -m pip install pyinstaller
    if %errorLevel% neq 0 (
        echo [ERRO] Falha ao instalar PyInstaller
        pause
        exit /b 1
    )
)

echo [OK] PyInstaller disponível

REM Instala dependências opcionais
echo [INFO] Instalando dependências opcionais...
python -m pip install requests pillow pystray plyer --quiet
echo [OK] Dependências instaladas

REM Limpa builds anteriores
echo [INFO] Limpando builds anteriores...
if exist "build" rmdir /S /Q "build" >nul 2>&1
if exist "dist" rmdir /S /Q "dist" >nul 2>&1
if exist "__pycache__" rmdir /S /Q "__pycache__" >nul 2>&1

REM Compila usando especificação melhorada
echo [INFO] Compilando cliente melhorado...
python -m PyInstaller client_agent_improved.spec --clean --noconfirm

if %errorLevel% == 0 (
    echo.
    echo ========================================
    echo  COMPILAÇÃO CONCLUÍDA COM SUCESSO!
    echo ========================================
    echo.
    echo Executável criado em: dist\JotanunesNotificationClient.exe
    echo.
    echo Para instalar:
    echo 1. Copie o executável para o computador de destino
    echo 2. Execute install_client.bat como administrador
    echo.
    echo Para distribuição via GPO:
    echo 1. Coloque os arquivos em um compartilhamento de rede
    echo 2. Configure GPO para executar install_client.bat
    echo.
    
    REM Testa o executável
    echo [INFO] Testando executável...
    if exist "dist\JotanunesNotificationClient.exe" (
        echo [OK] Executável criado com sucesso
        echo Tamanho: 
        dir "dist\JotanunesNotificationClient.exe" | find "JotanunesNotificationClient.exe"
    ) else (
        echo [ERRO] Executável não encontrado
    )
) else (
    echo.
    echo ========================================
    echo  ERRO NA COMPILAÇÃO!
    echo ========================================
    echo.
    echo Verifique os logs acima para detalhes do erro.
    echo.
)

pause
exit /b %errorLevel%

