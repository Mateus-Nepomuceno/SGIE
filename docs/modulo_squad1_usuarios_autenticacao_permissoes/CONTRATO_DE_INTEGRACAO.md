# Contrato de Integração Entre Módulos (Squads)

| Metadado | Detalhe |
|---|---|
| **Projeto** | SGIE — Sistema de Gestão de Inscrições e Eventos Universitários |
| **Módulo Provedor** | Usuários, Autenticação e Permissões (Squad 1) |
| **Módulos Consumidores** | Gestão de Eventos (Squad 2), Inscrições (Squad 3), Submissões e Financeiro |
| **Data de Criação** | 21 de setembro de 2026 |
| **Versão** | 1.0.0 |
| **Status** | Homologado para Implementação |

---

## 1. Visão Geral e Propósito

Este contrato de integração define as fronteiras, dependências, interfaces de código e contratos de dados entre o **Módulo de Usuários (Squad 1)** e os demais módulos do SGIE.

A elaboração deste documento consolida formalmente as respostas do Squad 1 às perguntas de alinhamento estabelecidas no planejamento da disciplina (`relatorio_de_atividades_squad1.pdf` e `ATA_REUNIAO.md`), assegurando que cada equipe possa trabalhar de forma autônoma sem gerar retrabalho ou acoplamentos indevidos.

---

## 2. Perguntas e Respostas Fundamentais de Integração

### 2.1 O que nosso módulo oferece?
1. **Cadastro e Gestão de Identidades**: Registro seguro com validação de dados civis obrigatórios (Nome, E-mail, CPF, Data de Nascimento e Telefone).
2. **Autenticação Unificada**: Suporte a login híbrido (CPF ou E-mail + Senha) e login federado via Conta Google.
3. **Recuperação Segura de Acesso**: Mecanismo de código numérico de 6 dígitos temporário despachado por e-mail para redefinição de senha sem intervenção de suporte.
4. **Gestão de Perfil Estendido de Organizadores**: Armazenamento de foto de perfil, banner e mini-biografia para qualificação de gestores de eventos (`RN04`).
5. **Matriz de Permissões e Papéis**: Verificação de papéis globais e contextuais (`PARTICIPANTE`, `AUTOR`, `AVALIADOR`, `ORGANIZADOR`, `PALESTRANTE`, `VOLUNTARIO`, `SUPORTE`).

### 2.2 De quais serviços externos nosso módulo depende?
1. **Servidor de E-mail (SMTP / Console)**: Responsável pelo transporte dos códigos de verificação de 6 dígitos.
   - Em desenvolvimento: `django.core.mail.backends.console.EmailBackend` (exibe o código no terminal).
   - Em produção: Servidor SMTP corporativo ou serviço transacional (SendGrid, Mailgun, Amazon SES).
2. **Provedor Google OAuth2**: Para autenticação com um clique de contas institucionais ou pessoais.

### 2.3 Quais dados precisamos receber dos demais módulos?
1. **Do Módulo de Eventos (Squad 2)**:
   - `evento_id` (inteiro): Identificador único do evento no momento em que um usuário se inscreve ou tem um papel contextual concedido.
2. **Do Módulo de Submissões e Avaliações**:
   - Sinalização de aprovação de artigos para confirmação/homologação de status de Autor de fato.
   - Designação de membros da banca para ativação de papel de Avaliador.

### 2.4 Quais dados fornecemos aos demais módulos (`RN06`)?
Conforme a regra de negócio `RN06`, os dados básicos de cadastro são compartilhados com todos os módulos do sistema. O Módulo de Usuários disponibiliza:
- `id` (int): Identificador unívoco do usuário.
- `nome_completo` (str): Para geração de credenciais, certificados e listas de presença.
- `email` (str): Para notificações de submissão, confirmações de pagamento e alertas de eventos.
- `cpf` (str): Para emissão de certificados acadêmicos oficiais com validade jurídica e notas fiscais/recibos no Módulo Financeiro.
- `data_nascimento` (date): Para validação de faixas etárias e categorias de inscrição.
- `telefone` (str): Para contatos de emergência e suporte no dia do evento.
- `identidade_sessao` (`request.user`): O objeto do usuário autenticado via sessão padrão do Django.

### 2.5 Quais regras pertencem exclusivamente ao nosso módulo?
1. `RN01`: Validação matemática de CPF e garantia de unicidade estrita de CPF e E-mail no banco de dados.
2. `RN02`: Garantia de herança de papéis (todo Autor e Avaliador é obrigatoriamente um Participante ativo).
3. `RN04`: Validação e persistência dos requisitos adicionais para promoção a Organizador de eventos.
4. Políticas de expiração e invalidação de códigos de recuperação de senha.

---

## 3. Interfaces Python (Service Layer) Expostas para os Demais Módulos

Para evitar acoplamento direto com o ORM interno de `usuarios`, o módulo expõe a classe `UsuarioService` com métodos públicos padronizados:

```python
from usuarios.services import UsuarioService

# 1. Obter dados cadastrais completos (RN06) para certificados ou financeiro
dados_usuario = UsuarioService.obter_dados_cadastrais(usuario_id=10)
# Retorno:
# {
#     "id": 10,
#     "nome_completo": "Ana Clara Santos",
#     "email": "ana.clara@universidade.edu.br",
#     "cpf": "123.456.789-00",
#     "data_nascimento": "2001-05-14",
#     "telefone": "(71) 98888-7777"
# }

# 2. Verificar se um usuário possui papel específico em um evento (RN03, RN05)
pode_avaliar = UsuarioService.verificar_papel_evento(usuario_id=10, evento_id=2, papel_esperado='AVALIADOR')  # Retorna True ou False

# 3. Atribuir ou homologar novo papel contextual a um usuário em um evento
UsuarioService.atribuir_papel_evento(usuario_id=10, evento_id=2, papel='AUTOR')

# 4. Verificar se o usuário está qualificado para criar eventos (RN04)
apto_a_criar_eventos = UsuarioService.is_organizador_homologado(usuario_id=10)
```

---

## 4. Segurança, Privacidade e Conformidade com a LGPD

1. **Minimização de Dados**: Módulos que precisam apenas verificar se o usuário está autenticado não devem requisitar CPF ou telefone.
2. **Dados Financeiros Sensíveis**: Conforme deliberado no item 2.3 da Ata de Reunião, dados financeiros e credenciais bancárias nunca são armazenados nas tabelas do Módulo de Usuários nem versionados no repositório.
3. **Senhas Criptografadas**: Senhas em texto puro nunca são expostas em logs, interfaces públicas ou APIs internas.
