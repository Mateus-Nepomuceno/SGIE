# Dicionário de Dados do Banco de Dados

| Metadado | Detalhe |
|---|---|
| **Projeto** | SGIE — Sistema de Gestão de Inscrições e Eventos Universitários |
| **Módulo** | Usuários, Autenticação e Permissões (Squad 1) |
| **Data de Criação** | 21 de setembro de 2026 |
| **Versão** | 1.0.0 |
| **SGBD Padrão** | SQLite (Desenvolvimento local) / PostgreSQL (Produção) |
| **Status** | Homologado para Implementação |

---

## 1. Visão Geral

Este documento descreve detalhadamente o esquema de tabelas, campos, tipos primitivos, restrições (*constraints*), chaves primárias, chaves estrangeiras e índices do **Módulo de Usuários**.

A estrutura foi planejada para garantir máxima integridade relacional, prevenir dados órfãos e indexar as colunas críticas de consulta e autenticação (`email` e `cpf`).

---

## 2. Tabelas do Domínio de Usuários

### 2.1 Tabela: `usuarios_usuario`
Armazena a identidade principal de todas as pessoas que interagem com o SGIE.

| Nome da Coluna | Tipo Django | Tipo SQL | Nulo? | Único? | Valor Padrão | Descrição / Regra de Negócio |
|---|---|---|:---:|:---:|---|---|
| `id` | `BigAutoField` | `BIGINT` | Não | Sim | Auto-incremento | Chave primária da tabela. |
| `nome_completo` | `CharField(150)` | `VARCHAR(150)` | Não | Não | — | Nome completo do usuário. |
| `email` | `EmailField(254)` | `VARCHAR(254)` | Não | Sim | — | E-mail corporativo ou pessoal (`RN01`). |
| `cpf` | `CharField(14)` | `VARCHAR(14)` | Não | Sim | — | CPF com 11 dígitos, único (`RN01`). |
| `data_nascimento` | `DateField` | `DATE` | Não | Não | — | Data de nascimento do usuário. |
| `telefone` | `CharField(20)` | `VARCHAR(20)` | Não | Não | — | Telefone/celular no formato nacional. |
| `password` | `CharField(128)` | `VARCHAR(128)` | Não | Não | — | Hash da senha gerado pelo Django. |
| `is_active` | `BooleanField` | `BOOLEAN` | Não | Não | `TRUE` | Indica se a conta de usuário está habilitada. |
| `is_staff` | `BooleanField` | `BOOLEAN` | Não | Não | `FALSE` | Concede acesso ao painel de administração. |
| `is_superuser` | `BooleanField` | `BOOLEAN` | Não | Não | `FALSE` | Concede todos os privilégios administrativos. |
| `last_login` | `DateTimeField` | `TIMESTAMP` | Sim | Não | `NULL` | Data e hora do último login realizado. |
| `date_joined` | `DateTimeField` | `TIMESTAMP` | Não | Não | `CURRENT_TIMESTAMP` | Data de criação do registro. |

**Índices e Restrições**:
- Chave Primária: `id`.
- Índice Único: `email` (`usuarios_usuario_email_uniq`).
- Índice Único: `cpf` (`usuarios_usuario_cpf_uniq`).

---

### 2.2 Tabela: `usuarios_perfilorganizador`
Contém as informações complementares necessárias para qualificação de organizadores de eventos (`RF04`, `RN04`).

| Nome da Coluna | Tipo Django | Tipo SQL | Nulo? | Único? | Valor Padrão | Descrição / Regra de Negócio |
|---|---|---|:---:|:---:|---|---|
| `id` | `BigAutoField` | `BIGINT` | Não | Sim | Auto-incremento | Chave primária. |
| `usuario_id` | `OneToOneField` | `BIGINT` | Não | Sim | — | Chave estrangeira para `usuarios_usuario.id`. |
| `foto_de_perfil` | `ImageField` | `VARCHAR(100)` | Sim | Não | `NULL` | Caminho do arquivo da foto de perfil. |
| `banner` | `ImageField` | `VARCHAR(100)` | Sim | Não | `NULL` | Caminho do arquivo do banner institucional. |
| `bio_do_organizador` | `TextField` | `TEXT` | Sim | Não | `NULL` | Mini-biografia descritiva do organizador. |
| `homologado` | `BooleanField` | `BOOLEAN` | Não | Não | `FALSE` | Status de aprovação institucional. |
| `atualizado_em` | `DateTimeField` | `TIMESTAMP` | Não | Não | `CURRENT_TIMESTAMP` | Data da última alteração de perfil. |

**Integridade Referencial**:
- `usuario_id` possui restrição `FOREIGN KEY (usuario_id) REFERENCES usuarios_usuario(id) ON DELETE CASCADE`.

---

### 2.3 Tabela: `usuarios_codigorecuperacao`
Registra os códigos emitidos para recuperação e redefinição de acesso (`RF03`).

| Nome da Coluna | Tipo Django | Tipo SQL | Nulo? | Único? | Valor Padrão | Descrição / Regra de Negócio |
|---|---|---|:---:|:---:|---|---|
| `id` | `BigAutoField` | `BIGINT` | Não | Sim | Auto-incremento | Chave primária. |
| `usuario_id` | `ForeignKey` | `BIGINT` | Não | Não | — | Chave estrangeira para `usuarios_usuario.id`. |
| `codigo` | `CharField(6)` | `VARCHAR(6)` | Não | Não | — | Código alfanumérico ou numérico de 6 dígitos. |
| `canal` | `CharField(20)` | `VARCHAR(20)` | Não | Não | `'EMAIL'` | Canal de entrega do código (E-mail / SMS). |
| `criado_em` | `DateTimeField` | `TIMESTAMP` | Não | Não | `CURRENT_TIMESTAMP` | Data e hora em que o código foi emitido. |
| `expira_em` | `DateTimeField` | `TIMESTAMP` | Não | Não | — | Data e hora de expiração (15 minutos). |
| `utilizado` | `BooleanField` | `BOOLEAN` | Não | Não | `FALSE` | Marcação de consumo de uso único. |

**Índices e Restrições**:
- Chave Primária: `id`.
- Índice Composto: `[usuario_id, codigo, utilizado]`.
- Integridade: `FOREIGN KEY (usuario_id) REFERENCES usuarios_usuario(id) ON DELETE CASCADE`.

---

### 2.4 Tabela: `usuarios_papelcontextual`
Tabela associativa para suportar a multiplicidade de papéis de um usuário por contexto de evento (`RN03`, `RN05`).

| Nome da Coluna | Tipo Django | Tipo SQL | Nulo? | Único? | Valor Padrão | Descrição / Regra de Negócio |
|---|---|---|:---:|:---:|---|---|
| `id` | `BigAutoField` | `BIGINT` | Não | Sim | Auto-incremento | Chave primária. |
| `usuario_id` | `ForeignKey` | `BIGINT` | Não | Não | — | Referência a `usuarios_usuario.id`. |
| `evento_id` | `PositiveBigIntegerField` | `BIGINT` | Não | Não | — | Referência ao identificador do evento (Squad 2). |
| `papel` | `CharField(20)` | `VARCHAR(20)` | Não | Não | `'PARTICIPANTE'` | Enum: `PARTICIPANTE`, `AUTOR`, `AVALIADOR`, etc. |
| `ativo` | `BooleanField` | `BOOLEAN` | Não | Não | `TRUE` | Situação da homologação do papel no evento. |
| `atribuido_em` | `DateTimeField` | `TIMESTAMP` | Não | Não | `CURRENT_TIMESTAMP` | Data em que o papel foi concedido. |

**Índices e Restrições**:
- Restrição Única Composta (`unique_together`): `(usuario_id, evento_id, papel)`.
- Previne duplicidade de concessão do mesmo papel para um usuário em um mesmo evento.
