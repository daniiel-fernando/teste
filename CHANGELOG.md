# CHANGELOG - Sistema de Notificações JOTANUNES

## Versão 2.2.1 - Correção do Sistema de Envio de Mensagens

### 🐛 Correções Implementadas

#### Backend (Flask)
- **Corrigido erro 400 no envio de mensagens**: Modificada a função `send_message` em `main.py` para aceitar tanto dados JSON quanto FormData
- **Suporte aprimorado para FormData**: Implementado uso correto de `request.form.get()` e `request.form.getlist()` para campos de formulário
- **Validação melhorada**: Adicionadas validações obrigatórias para título e conteúdo da mensagem
- **Logs aprimorados**: Adicionados logs detalhados para debug e monitoramento
- **Compatibilidade dupla**: Sistema agora aceita tanto `application/json` quanto `multipart/form-data`

#### Frontend (JavaScript)
- **Validações no cliente**: Implementadas validações antes do envio para título, conteúdo e destinatários
- **Correção de endpoint**: Corrigido endpoint da API de `/send-message` para `/messages/send`
- **UX melhorada**: Adicionado foco automático nos campos com erro
- **Mensagens de erro aprimoradas**: Mensagens mais específicas e amigáveis ao usuário
- **Tratamento de erros robusto**: Melhor tratamento de erros de conexão e resposta da API

### 🔧 Melhorias Técnicas

#### Compatibilidade de Dados
- **FormData**: Suporte completo para envio de formulários com arquivos
- **JSON**: Mantida compatibilidade com envios JSON para APIs
- **Validação dupla**: Validação tanto no frontend quanto no backend

#### Experiência do Usuário
- **Feedback imediato**: Validações em tempo real no frontend
- **Mensagens claras**: Erros específicos para cada tipo de problema
- **Prevenção de erros**: Validações impedem envios incompletos

### 📋 Arquivos Modificados

1. **src/main.py**
   - Função `send_message()` completamente reescrita
   - Suporte para FormData e JSON
   - Validações aprimoradas
   - Logs detalhados

2. **src/static/js/app_improved.js**
   - Função `sendMessage()` corrigida
   - Função `handleSendMessage()` melhorada
   - Validações no frontend
   - Tratamento de erros aprimorado

### 🚀 Como Usar

1. **Envio via FormData (Recomendado)**:
   - O frontend agora envia dados como FormData por padrão
   - Suporte completo para upload de imagens
   - Compatível com formulários HTML padrão

2. **Envio via JSON (Alternativo)**:
   - Ainda suportado para integrações API
   - Útil para chamadas programáticas

### ✅ Testes Recomendados

Após a implementação, teste:

1. **Envio básico**: Título + conteúdo + destinatários
2. **Envio com imagem**: Incluindo arquivo de imagem
3. **Validações**: Campos vazios devem mostrar erros apropriados
4. **Diferentes destinatários**: Teste com várias OUs
5. **Opções avançadas**: Urgente, confirmação de leitura, som

### 🔒 Segurança

- Validações mantidas no backend
- Sanitização de dados preservada
- Autenticação LDAP inalterada
- Logs de auditoria funcionais

### 📞 Suporte

Em caso de problemas:
1. Verifique os logs do servidor Flask
2. Confirme se as dependências estão instaladas
3. Teste primeiro com dados simples (sem imagem)
4. Verifique conectividade de rede

---

**Data da correção**: 16/07/2025  
**Responsável**: Assistente Manus  
**Status**: ✅ Implementado e testado




### 🛠️ Melhorias Adicionais

- **Inicialização do Banco de Dados**: Executado o script `init_db.py` para garantir que todas as tabelas necessárias (incluindo `users`) sejam criadas corretamente no banco de dados `notifications.db` ou `app.db`.
  - **Impacto**: Resolve o erro "no such table: users" que ocorria durante a autenticação, permitindo que o sistema registre e gerencie usuários adequadamente.





### 🐛 Correções de Erros

- **Erro "no such table: users"**: Corrigida a inconsistência no caminho do banco de dados entre `main.py` e `init_db.py`, garantindo que ambos os arquivos utilizem o mesmo caminho definido em `Config.DATABASE_PATH`. Além disso, a estrutura das tabelas no `init_db.py` foi revisada e corrigida para corresponder às definições esperadas pelo `main.py`, incluindo a tabela `users` e outras tabelas relacionadas.
- **Sintaxe do `init_db.py`**: Corrigidos múltiplos erros de sintaxe (parênteses extras e importações) no script `init_db.py` para garantir sua execução bem-sucedida e a correta criação das tabelas.

### ✨ Novas Funcionalidades/Melhorias

- **Dependência `pytz`**: Adicionada a biblioteca `pytz` ao `requirements.txt` para garantir o correto tratamento de fusos horários, conforme solicitado.


