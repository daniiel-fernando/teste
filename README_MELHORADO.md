# Sistema de Notificações Corporativas - Jotanunes
## Versão 2.1.0 - Melhorada e Corrigida

### 🚀 Melhorias Implementadas

#### ✅ Problemas Corrigidos do Agente Python
- **Dependências atualizadas**: Corrigidos problemas de compatibilidade
- **Instalação simplificada**: Scripts automáticos para Windows (.bat)
- **Compilação melhorada**: Novo arquivo .spec para PyInstaller sem erros
- **Tratamento de erros**: Melhor gestão de exceções e logs
- **Configuração robusta**: Arquivo de configuração mais flexível

#### ✅ Interface Moderna e Responsiva
- **Design atualizado**: Interface moderna com cores corporativas Jotanunes
- **Responsividade**: Funciona perfeitamente em desktop e mobile
- **UX melhorada**: Navegação intuitiva e feedback visual
- **Tema escuro/claro**: Alternância entre temas
- **Animações suaves**: Transições e efeitos visuais

#### ✅ Opções Específicas de OUs (Conforme Solicitado)
- **Todas as OUs**: Envio para todos os departamentos
- **TI / Tecnologia**: Departamento de TI específico
- **Operacional**: Equipes de campo e produção
- **Gestores**: Coordenadores e supervisores
- **Diretoria**: Diretores e alta gestão

#### ✅ Funcionalidades Adicionais
- **Upload de imagens**: Suporte a PNG, JPG, GIF (até 16MB)
- **Mensagens urgentes**: Opção de prioridade alta
- **Confirmação de leitura**: Rastreamento de entrega
- **Agendamentos**: Sistema de mensagens programadas
- **Histórico completo**: Registro de todas as mensagens
- **Relatórios**: Analytics e estatísticas

### 📋 Requisitos do Sistema

#### Servidor (Windows/Linux)
- Python 3.8 ou superior
- Flask 3.1.1
- SQLite 3
- 2GB RAM mínimo
- 10GB espaço em disco

#### Clientes (Windows)
- Windows 10/11
- .NET Framework 4.7.2+
- 512MB RAM
- Conexão de rede com o servidor

### 🔧 Instalação do Servidor

#### 1. Preparação do Ambiente
```bash
# Clone ou extraia os arquivos
cd sistema-corrigido

# Instale as dependências
pip install -r requirements.txt
```

#### 2. Configuração
```bash
# Edite o arquivo config.py conforme necessário
# Configure a conexão LDAP/AD
# Defina as OUs e departamentos
```

#### 3. Execução
```bash
# Servidor de desenvolvimento
python src/main_improved.py

# Servidor de produção (recomendado)
gunicorn -w 4 -b 0.0.0.0:5000 src.main_improved:create_app()
```

### 🖥️ Instalação do Cliente (Agente Python)

#### Opção 1: Executável Pré-compilado
1. Execute `install_client.bat` como administrador
2. O agente será instalado automaticamente
3. Configuração via GPO disponível

#### Opção 2: Compilação Manual
```bash
# Instale dependências
pip install -r client_requirements_improved.txt

# Compile o executável
python -m PyInstaller client_agent_improved.spec

# O executável estará em dist/
```

### 🌐 Acesso ao Sistema

1. **URL**: http://seu-servidor:5000
3. **Produção**: Configure autenticação LDAP/AD

### 📱 Como Usar

#### Enviar Mensagens
1. Acesse a aba "Enviar Mensagens"
2. Selecione os destinatários (OUs específicas)
3. Digite título e conteúdo
4. Adicione imagem se necessário
5. Configure opções (urgente, confirmação, som)
6. Clique em "Enviar Mensagem"

#### Gerenciar Computadores
1. Aba "Computadores" mostra todos os clientes
2. Filtros por departamento e status
3. Informações em tempo real

#### Histórico e Relatórios
1. Aba "Histórico" para mensagens enviadas
2. Aba "Relatórios" para analytics
3. Exportação de dados disponível

### 🔒 Segurança

- **Autenticação LDAP/AD**: Integração com Active Directory
- **Sessões seguras**: Controle de acesso baseado em roles
- **Logs auditoria**: Registro completo de atividades
- **Validação de entrada**: Proteção contra XSS e injection
- **HTTPS**: Suporte a SSL/TLS (configure certificados)

### 🛠️ Configuração LDAP/AD

Edite o arquivo `config.py`:

```python
LDAP_CONFIG = {
    'server': 'ldap://seu-servidor-ad.empresa.com',
    'base_dn': 'DC=empresa,DC=com',
    'user_dn': 'CN=Users,DC=empresa,DC=com',
    'bind_user': 'usuario-servico@empresa.com',
    'bind_password': 'senha-servico',
    'departments': {
        'TI': 'OU=TI,DC=empresa,DC=com',
        'OPERACIONAL': 'OU=Operacional,DC=empresa,DC=com',
        'GESTORES': 'OU=Gestores,DC=empresa,DC=com',
        'DIRETORIA': 'OU=Diretoria,DC=empresa,DC=com'
    }
}
```

### 📊 Monitoramento

#### Logs do Sistema
- `notifications_server.log`: Logs do servidor
- `client_agent.log`: Logs dos clientes
- `database.log`: Logs do banco de dados

#### Métricas Disponíveis
- Computadores online/offline
- Mensagens enviadas/entregues
- Taxa de leitura por departamento
- Performance do sistema

### 🔄 Backup e Manutenção

#### Backup Automático
```bash
# Script de backup incluído
./scripts/backup_database.sh

# Backup manual
cp notifications.db backup/notifications_$(date +%Y%m%d).db
```

#### Manutenção
- Limpeza automática de logs antigos
- Otimização do banco de dados
- Monitoramento de espaço em disco

### 🆘 Solução de Problemas

#### Problemas Comuns

**1. Agente não conecta**
- Verifique firewall (porta 5000)
- Confirme IP do servidor
- Teste conectividade de rede

**2. Autenticação LDAP falha**
- Verifique configurações LDAP
- Teste credenciais do usuário de serviço
- Confirme conectividade com AD

**3. Interface não carrega**
- Verifique se o servidor está executando
- Confirme porta 5000 disponível
- Teste em navegador diferente

**4. Mensagens não chegam**
- Verifique se clientes estão online
- Confirme seleção de destinatários
- Verifique logs do servidor

### 📞 Suporte

Para suporte técnico:
- **Email**: suporte@jotanunes.net
- **Documentação**: Wiki interno da empresa
- **Logs**: Sempre inclua logs relevantes

### 📝 Changelog

#### Versão 2.1.0 (Atual)
- ✅ Interface moderna e responsiva
- ✅ Opções específicas de OUs
- ✅ Agente Python corrigido
- ✅ Melhor tratamento de erros
- ✅ Sistema de logs aprimorado
- ✅ Suporte a imagens
- ✅ Tema escuro/claro
- ✅ Instalação simplificada

#### Versão 2.0.0 (Anterior)
- Sistema básico de notificações
- Interface simples
- Problemas de compatibilidade

### 🔮 Próximas Versões

#### Versão 2.2.0 (Planejada)
- [ ] Notificações push mobile
- [ ] API REST completa
- [ ] Dashboard executivo
- [ ] Integração com Teams/Slack
- [ ] Mensagens em vídeo
- [ ] Chatbot integrado

### 📄 Licença

Sistema proprietário da Jotanunes.
Todos os direitos reservados.

---

**Desenvolvido com ❤️ para Jotanunes**
*Versão 2.1.0 - Dezembro 2024*

