# -*- mode: python ; coding: utf-8 -*-
"""
Especificação melhorada para PyInstaller - Cliente de Notificações Jotanunes
Versão 2.1.0 - Corrigida para instalação robusta
"""

import os
import sys

# Adiciona o diretório do projeto ao path
project_dir = os.path.dirname(os.path.abspath(SPEC))
sys.path.insert(0, project_dir)

# Dados adicionais para incluir no executável
added_files = []

# Inclui logos e ícones se existirem
logo_files = [
    ('jnunes_logo.png', '.'),
    ('LogoVermelha-Branca.png', '.'),
    ('Logo.JOTA.3.ico', '.')
]

for logo_file, dest in logo_files:
    logo_path = os.path.join(project_dir, logo_file)
    if os.path.exists(logo_path):
        added_files.append((logo_path, dest))

# Inclui arquivos de configuração se existirem
config_files = [
    ('config.py', '.'),
    ('client_requirements.txt', '.')
]

for config_file, dest in config_files:
    config_path = os.path.join(project_dir, config_file)
    if os.path.exists(config_path):
        added_files.append((config_path, dest))

# Módulos ocultos necessários
hidden_imports = [
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'json',
    'urllib.request',
    'urllib.parse',
    'urllib.error',
    'socket',
    'platform',
    'threading',
    'time',
    'datetime',
    'logging',
    'uuid',
    'getpass',
    'subprocess',
    'webbrowser',
    'io',
    'base64',
    'os',
    'sys'
]

# Adiciona módulos opcionais se disponíveis
optional_imports = [
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'pystray',
    'requests'
]

# Verifica quais módulos opcionais estão disponíveis
for module in optional_imports:
    try:
        __import__(module)
        hidden_imports.append(module)
    except ImportError:
        pass

a = Analysis(
    ['src/utils/client_agent_improved.py'],
    pathex=[project_dir],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclui módulos desnecessários para reduzir tamanho
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'IPython',
        'jupyter',
        'notebook',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx'
    ],
    noarchive=False,
    optimize=2,  # Otimização máxima
)

# Remove duplicatas
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='JotanunesNotificationClient',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compressão UPX
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Sem console para interface gráfica
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_dir, 'Logo.JOTA.3.ico') if os.path.exists(os.path.join(project_dir, 'Logo.JOTA.3.ico')) else None,
    version_file=None,
    uac_admin=False,  # Não requer privilégios de administrador
    uac_uiaccess=False,
)

# Informações sobre o build
print(f"""
=== Build Information ===
Project Directory: {project_dir}
Added Files: {len(added_files)}
Hidden Imports: {len(hidden_imports)}
Output: JotanunesNotificationClient.exe
=========================
""")

