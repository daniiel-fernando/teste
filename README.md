# Sistema de Notificações Corporativas - Jotanunes
## Versão Melhorada com Suporte a Imagens, Agendamento e Controle de Acesso

### 🚀 Funcionalidades Implementadas

#### ✅ Funcionalidades Principais
- **Envio de Mensagens**: Suporte completo para texto e imagens
- **Sistema de Agendamento**: Agende mensagens para envio automático
- **Filtro por Computador**: Envie notificações para computadores específicos
- **Controle de Acesso AD**: Apenas usuários do grupo GG_TECNOLOGIA podem acessar
- **Modo Dark**: Interface moderna com alternância entre temas claro e escuro
- **Logos Integradas**: Logos da Jotanunes integradas conforme solicitado
- **Interface Responsiva**: Funciona perfeitamente em desktop e mobile
- **Agente Cliente**: Software para instalação nas máquinas via GPO

#### 🔐 Segurança e Controle de Acesso
- **Active Directory**: Integração completa com AD da Jotanunes
- **Grupo GG_TECNOLOGIA**: Apenas usuários deste grupo podem acessar o sistema
- **Autenticação Segura**: Validação de credenciais via LDAP/AD
- **Sessões Seguras**: Controle de sessão com timeout automático

#### 💻 Filtro por Computador
- **Registro Automático**: Computadores se registram automaticamente
- **Heartbeat**: Monitoramento de status online/offline
- **Notificações Direcionadas**: Envie mensagens para computadores específicos
- **Departamentos**: Organização por departamentos (TI, Operacional, Gestores, Diretoria)

#### 🎨 Interface Moderna
- Design moderno e intuitivo
- Modo dark/light com persistência
- Cores corporativas da Jotanunes
- Animações suaves e feedback visual
- Layout responsivo

#### 📅 Sistema de Agendamento
- Agende mensagens para horários específicos
- Frequências: Todos os dias, Dias úteis, Fins de semana
- Controle de ativação/desativação
- Histórico de envios
- Próximos envios programados

### 🛠️ Tecnologias Utilizadas

#### Backend
- **Flask 3.1.1**: Framework web Python
- **SQLAlchemy**: ORM para banco de dados
- **APScheduler**: Sistema de agendamento
- **Flask-CORS**: Suporte a CORS
- **ldap3**: Integração com Active Directory
- **Pillow**: Processamento de imagens
- **SQLite**: Banco de dados

#### Frontend
- **HTML5/CSS3**: Interface moderna
- **JavaScript ES6+**: Funcionalidades interativas
- **Font Awesome**: Ícones
- **CSS Grid/Flexbox**: Layout responsivo

#### Cliente
- **Python 3.11+**: Agente cliente
- **Tkinter**: Interface gráfica
- **Pillow**: Processamento de imagens
- **Requests**: Comunicação HTTP
- **pystray**: Ícone na bandeja do sistema

### 📁 Estrutura do Projeto

```
sistema-melhorado/
├── src/
│   ├── models/           # Modelos do banco de dados
│   │   ├── user.py
│   │   ├── message.py
│   │   ├── scheduled_message.py
│   │   └── computer.py   # NOVO: Modelo para computadores
│   ├── routes/           # Rotas da API
│   │   ├── auth.py       # Autenticação original
│   │   ├── auth_demo.py  # Autenticação demo
│   │   ├── auth_ad.py    # NOVO: Autenticação AD com grupo
│   │   ├── user.py
│   │   ├── message.py
│   │   ├── schedule.py
│   │   └── computer.py   # NOVO: Gerenciamento de computadores
│   ├── static/           # Arquivos estáticos
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── templates/        # Templates HTML
│   ├── utils/            # Utilitários
│   │   ├── scheduler.py
│   │   ├── ad_auth.py    # NOVO: Utilitário para AD
│   │   └── client_agent.py # NOVO: Agente cliente
│   └── main.py          # Aplicação principal
├── uploads/             # Upload de imagens
├── config.py           # NOVO: Configurações centralizadas
├── requirements.txt     # Dependências do servidor
├── client_requirements.txt # NOVO: Dependências do cliente
├── create_demo_user.py  # Script para criar usuário demo
└── README.md           # Esta documentação
```

### 🚀 Como Executar

#### 1. Servidor Central

##### Instalar Dependências
```bash
cd sistema-melhorado
pip install -r requirements.txt
```

##### Configurar Active Directory
```bash
# Variáveis de ambiente (opcional)
export AD_SERVER_URL="ldap://dc.jotanunes.net"
export AD_DOMAIN="JOTANUNES.NET"
export AD_BASE_DN="DC=jotanunes,DC=net"
export AD_TECH_GROUP="GG_TECNOLOGIA"
```

##### Executar Servidor
```bash
python src/main.py
```

#### 2. Cliente (Agente)

##### Instalar Dependências
```bash
pip install -r client_requirements.txt
```

##### Executar Cliente
```bash
python src/utils/client_agent.py
```

#### 3. Acessar o Sistema
- URL: http://localhost:5000
- Acesso: Apenas usuários do grupo GG_TECNOLOGIA

### 📋 Funcionalidades Detalhadas

#### 🔐 Sistema de Autenticação AD
- **Integração Completa**: Conecta diretamente ao Active Directory da Jotanunes
- **Grupo GG_TECNOLOGIA**: Apenas usuários deste grupo podem acessar
- **Validação Automática**: Verifica automaticamente a pertinência ao grupo
- **Fallback Seguro**: Sistema falha de forma segura se AD não estiver disponível
- **Sincronização**: Dados do usuário são sincronizados com o AD

#### 💻 Gerenciamento de Computadores
- **Auto-Registro**: Computadores se registram automaticamente ao executar o agente
- **Heartbeat**: Monitoramento contínuo de status (online/offline)
- **Informações Detalhadas**:
  - Nome do computador
  - Endereço IP
  - Endereço MAC
  - Departamento
  - Usuário logado
  - Última atividade
- **Filtros Avançados**: Envie mensagens para computadores específicos ou departamentos

#### 💬 Envio de Mensagens Aprimorado
- **Destinatários Flexíveis**: 
  - Por departamento
  - Por computadores específicos
  - Combinação de ambos
- **Tipos de Mensagem**:
  - Texto simples
  - Imagens (PNG, JPG, GIF até 16MB)
  - Texto + imagem
- **Histórico Completo**: Registro de todas as mensagens enviadas

#### ⏰ Sistema de Agendamento Avançado
- **Horários Específicos**: Defina hora exata (ex: 17:30)
- **Frequências Flexíveis**: 
  - Todos os dias
  - Apenas dias úteis
  - Apenas fins de semana
- **Controles Completos**:
  - Ativar/Desativar agendamentos
  - Excluir agendamentos
  - Visualizar próximos envios
  - Histórico de execuções
- **Persistência**: Agendamentos sobrevivem a reinicializações

#### 🖥️ Agente Cliente
- **Interface Gráfica**: Notificações visuais atrativas
- **Bandeja do Sistema**: Ícone discreto na bandeja
- **Auto-Inicialização**: Pode ser configurado para iniciar com o Windows
- **Logs Detalhados**: Registro completo de atividades
- **Configuração Automática**: Detecta departamento baseado no nome do computador

### 🔧 Configurações de Produção

#### Variáveis de Ambiente
```bash
# Active Directory
AD_SERVER_URL=ldap://dc.jotanunes.net
AD_DOMAIN=JOTANUNES.NET
AD_BASE_DN=DC=jotanunes,DC=net
AD_TECH_GROUP=GG_TECNOLOGIA

# Banco de Dados
DATABASE_URL=postgresql://user:pass@localhost/notifications

# Segurança
SECRET_KEY=sua-chave-secreta-aqui
FLASK_ENV=production

# Upload
UPLOAD_FOLDER=/var/uploads
MAX_CONTENT_LENGTH=16777216

# Agendamento
SCHEDULER_TIMEZONE=America/Sao_Paulo
```

#### Deployment via GPO

##### 1. Preparar Executável
```bash
# Instalar PyInstaller
pip install pyinstaller

# Criar executável
pyinstaller --onefile --windowed --icon=logo.ico src/utils/client_agent.py
```

##### 2. Configurar GPO
1. Copie o executável para um compartilhamento de rede
2. Configure GPO para executar na inicialização
3. Adicione ao registro para inicialização automática
4. Configure firewall para permitir comunicação

##### 3. Script de Instalação
```batch
@echo off
REM Script de instalação do agente cliente
copy "\\servidor\compartilhamento\client_agent.exe" "C:\Program Files\Jotanunes\NotificationClient\"
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "JotanunesNotifications" /t REG_SZ /d "C:\Program Files\Jotanunes\NotificationClient\client_agent.exe" /f
sc create "JotanunesNotifications" binPath= "C:\Program Files\Jotanunes\NotificationClient\client_agent.exe" start= auto
sc start "JotanunesNotifications"
```

### 🔒 Segurança

#### Implementado
- Autenticação via Active Directory
- Validação de grupo GG_TECNOLOGIA
- Validação de uploads
- Sanitização de inputs
- Controle de sessões
- CORS configurado
- Logs de auditoria
- Comunicação HTTPS (recomendado)

#### Recomendações para Produção
- HTTPS obrigatório
- Rate limiting
- Backup automático
- Monitoramento
- Atualizações de segurança
- Firewall configurado
- Certificados SSL válidos

### 📊 Monitoramento

#### Logs do Sistema
- Autenticações
- Envio de mensagens
- Agendamentos executados
- Registros de computadores
- Erros e exceções

#### Métricas Disponíveis
- Computadores online/offline
- Mensagens enviadas por período
- Agendamentos ativos
- Usuários ativos
- Departamentos mais ativos

### 🆘 Solução de Problemas

#### Problemas Comuns

##### Active Directory não conecta
1. Verifique conectividade de rede
2. Confirme configurações de DNS
3. Valide credenciais de serviço
4. Verifique firewall

##### Cliente não recebe notificações
1. Verifique se o agente está executando
2. Confirme conectividade com servidor
3. Valide registro do computador
4. Verifique logs do cliente

##### Agendamentos não executam
1. Verifique se o scheduler está ativo
2. Confirme timezone configurado
3. Valide permissões de banco
4. Verifique logs do servidor

### 📞 Suporte

Para dúvidas ou suporte técnico:
- Email: ti@jotanunes.net
- Telefone: (79) XXXX-XXXX
- Sistema interno: http://notifications.jotanunes.net

### 📝 Changelog

#### Versão 2.0.0
- ✅ Filtro por computador específico
- ✅ Restrição de acesso via grupo GG_TECNOLOGIA
- ✅ Agente cliente para instalação via GPO
- ✅ Monitoramento de computadores online/offline
- ✅ Heartbeat automático
- ✅ Interface aprimorada
- ✅ Configurações centralizadas
- ✅ Logs detalhados

#### Versão 1.0.0
- ✅ Envio de mensagens texto e imagem
- ✅ Sistema de agendamento
- ✅ Modo dark/light
- ✅ Logos integradas
- ✅ Interface responsiva

---

**Desenvolvido para Jotanunes Construtora**  
*Sistema de Notificações Corporativas v2.0*

