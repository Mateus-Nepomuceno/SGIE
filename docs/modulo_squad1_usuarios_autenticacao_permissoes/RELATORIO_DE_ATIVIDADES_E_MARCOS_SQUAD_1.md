# Relatório de Atividades e Marcos — Squad 1

| Metadado | Detalhe |
|---|---|
| **Projeto** | SGIE — Sistema de Gestão de Inscrições e Eventos Universitários |
| **Squad** | Squad 1: Usuários, Autenticação e Permissões |
| **Integrantes** | Gabriele Natividade, Letícia Farias, Letícia Vitorino e Luciano de Souza |
| **Líder do Squad** | Luciano de Souza |
| **Período de Atuação** | 20/08/2026 a 26/08/2026 (Modelagem) e 21/09/2026 (Formalização/MVP) |
| **Versão** | 1.0.0 |
| **Status** | Homologado |

---

## 1. Escopo e Atribuições do Squad 1

O **Squad 1** é responsável por projetar, modelar, documentar e implementar o módulo primordial do sistema de eventos universitários: o gerenciamento de identidades, credenciais, perfis e matriz de autorização por papel.

Como primeiro elo da cadeia de dependências do projeto (conforme estabelecido no item 2.5 da Ata de Reunião de Líderes), o Squad 1 fornece a base de autenticação e os dados de usuários sobre os quais operam a Gestão de Eventos (Squad 2), Inscrições (Squad 3), Submissões e Financeiro.

---

## 2. Divisão de Responsabilidades da Equipe

Em alinhamento com os registros iniciais do projeto (`desenvolvimento_inicial_projeto_marcos.pdf` e `relatorio_de_atividades_squad1.pdf`), as atribuições foram distribuídas da seguinte forma entre os membros da equipe:

| Integrante | Papel / Responsabilidade Primária | Entregável Principal |
|---|---|---|
| **Gabriele Natividade (Gab)** | Engenharia de Requisitos | Levantamento detalhado de 8 Requisitos Funcionais (`RF01`–`RF08`) e 6 Regras de Negócio (`RN01`–`RN06`). |
| **Letícia Vitorino (Vitorino)** | Modelagem de Casos de Uso | Mapeamento dos 5 atores do sistema, relações de herança, inclusão/extensão e diagrama comportamental. |
| **Letícia Farias (Veras)** | Modelagem Conceitual de Classes | Mapeamento de entidades de dados (`Usuario`, `Organizador`, `CodigoRecuperacao`, `Papel`), atributos e cardinalidades. |
| **Luciano de Souza** | Liderança Técnica e Arquitetura | Diagramas de Sequência de Cadastro e Login, coordenação geral do squad, alinhamento técnico com as demais equipes e arquitetura Django. |

---

## 3. Marcos e Atividades Realizadas

### Marco 1 — Levantamento de Requisitos e Regras de Negócio (Concluído)
- Identificação dos atores fundamentais: Não Autenticado, Participante, Autor, Avaliador e Organizador/ADM.
- Definição dos campos civis obrigatórios para cadastro: Nome completo, E-mail, CPF, Data de Nascimento e Telefone.
- Consolidação das 6 regras de negócio fundamentais:
  - `RN01`: Unicidade de CPF e e-mail.
  - `RN02`: Herança conceitual de papéis especiais (Autores e Avaliadores são sempre Participantes).
  - `RN03`: Multiplicidade de papéis contextuais por evento.
  - `RN04`: Requisitos de promoção a Organizador (foto, banner e biografia institucional).
  - `RN05`: Restrição de submissão e avaliação por papel homologado.
  - `RN06`: Disponibilização dos dados básicos aos demais módulos.

### Marco 2 — Modelagem Estrutural e Comportamental (Concluído)
- Elaboração do diagrama conceitual de classes com cardinalidades detalhadas.
- Elaboração do diagrama de casos de uso cobrindo desde o acesso anônimo até a gestão de bancas.
- Elaboração do diagrama de sequência evidenciando a validação e fluxo de persistência de senhas criptografadas.

### Marco 3 — Formalização em Markdown no Repositório (Concluído)
- Transposição integral de todos os diagramas e relatórios gráficos para código versionável em Markdown com suporte nativo a diagramas Mermaid.
- Padronização de nomes de arquivos em maiúsculas com underscore (`LETRAS_MAIUSCULAS_E_UNDERSCORE.md`) em conformidade com as diretrizes do projeto.

### Marco 4 — Alinhamento e Contrato de Integração (Concluído)
- Definição das respostas formais aos demais squads (o que oferecemos, do que dependemos, o que recebemos e quais regras são de nossa responsabilidade exclusiva).
- Exposição da camada de serviços (`UsuarioService`) para consumo transparente por Eventos, Inscrições e Financeiro.

---

## 4. Próximos Passos e Cronograma até o MVP

| Data | Atividade Planejada | Responsável |
|:---:|---|---|
| **21/09 (Seg)** | Configuração do molde Django e formalização dos artefatos em `docs/` | Mateus e Luciano |
| **22/09 (Ter)** | Implementação completa do módulo `usuarios/` (models, forms, views, templates Fase 1 e testes) | Squad 1 |
| **23/09 (Qua)** | Dia reservado para estudos e prova acadêmica (sem desenvolvimento obrigatório) | Todos |
| **24/09 (Qui)** | Disponibilização do módulo homologado para consumo do Squad 2 (Eventos) | Squad 1 e Squad 2 |
| **27/09 (Dom)** | Testes de integração geral e resolução de inconsistências entre módulos | Todos os líderes |
| **28/09 (Seg)** | Aplicação da camada de estilização CSS/Design unificado | Equipe de Front-end |
| **29/09 (Ter)** | **Apresentação Oficial do MVP para a Professora Marta** | Todos os squads |
