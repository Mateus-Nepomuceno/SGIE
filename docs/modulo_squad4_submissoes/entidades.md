# Especificacao do Modelo de Dados - Modulo de Submissao

## Visao Geral
Este documento descreve o modelo de banco de dados relacional corrigido e expandido para o Modulo de Submissao de Trabalhos Academicos. Foram eliminadas as redundancias estruturais (como a duplicacao da entidade de Organizador), adicionada a chave estrangeira obrigatoria para eventos, inseridos os campos de perfil profissional (Lattes e LinkedIn), e estruturado o suporte para o historico de versoes de correcoes (re-submissoes) e pareceres multiplos.

---

## 1. Enums e Tipos de Dados Globais

### Enum tipo_submissao
* ARTIGO
* PALESTRA
* MINICURSO
* POSTER
* OUTRO

### Enum status_submissao
* RASCUNHO
* SUBMETIDA
* EM_AVALIACAO
* CORRECOES_SOLICITADAS
* APROVADA
* REJEITADA

### Enum tipo_participacao_autor
* PRINCIPAL
* COAUTOR

---

## 2. Dicionario de Dados das Entidades

### Entidade: Usuario
Representa os cadastros de usuarios do sistema (autores, coautores, avaliadores e organizadores), eliminando a tabela separada e redundante de organizador.
* `id`: uuid (Chave Primaria)
* `nome`: varchar (Obrigatorio)
* `email`: varchar (Obrigatorio, Unico)
* `lattes`: varchar (Opcional, Link do curriculo Lattes)
* `linkedin`: varchar (Opcional, Link do perfil profissional LinkedIn)
* `afiliacao_institucional`: varchar (Opcional, Universidade ou instituicao de vinculo)
* `created_at`: timestamp (Obrigatorio)

### Entidade: Area
Representa as grandes areas tematicas ou eixos do evento.
* `id`: uuid (Chave Primaria)
* `nome`: varchar (Obrigatorio)
* `descricao`: text (Opcional)

### Entidade: Submissao
Representa o trabalho acadêmico submetido, contendo os metadados principais e vinculos estruturais.
* `id`: uuid (Chave Primaria)
* `evento_id`: uuid (Chave Estrangeira obrigatoria vinculada ao Modulo de Eventos)
* `autor_principal_id`: uuid (Chave Estrangeira para Usuario, autor responsavel pelo envio)
* `area_id`: uuid (Chave Estrangeira para Area)
* `titulo`: varchar (Obrigatorio)
* `descricao`: text (Opcional)
* `abstract`: text (Obrigatorio, resumo em ingles ou portugues conforme normas)
* `resumo`: text (Opcional)
* `keywords`: varchar (Obrigatorio, palavras-chave separadas por virgula)
* `tipo`: tipo_submissao (Obrigatorio)
* `status`: status_submissao (Obrigatorio, padrao: RASCUNHO)
* `created_at`: timestamp (Obrigatorio)
* `updated_at`: timestamp (Obrigatorio)

### Entidade: SubmissaoAutor (Relacionamento N para N de Autoria)
Permite vincular multiplos autores e coautores a uma submissao, registrando o papel de cada um para fins de certificacao.
* `id`: uuid (Chave Primaria)
* `submissao_id`: uuid (Chave Estrangeira para Submissao)
* `usuario_id`: uuid (Chave Estrangeira para Usuario)
* `tipo_participacao`: tipo_participacao_autor (Obrigatorio: PRINCIPAL ou COAUTOR)
* `ordem_autoria`: integer (Opcional, para ordenacao nos certificados)

### Entidade: SubmissaoVersao (Historico de Correcoes e Re-submissoes)
Permite armazenar o historico de arquivos e submissoes quando o trabalho passa pelo estado de "CORRECOES_SOLICITADAS" e precisa ser enviado novamente.
* `id`: uuid (Chave Primaria)
* `submissao_id`: uuid (Chave Estrangeira para Submissao)
* `numero_versao`: integer (Obrigatorio, ex: 1 para original, 2 para revisado)
* `caminho_arquivo`: varchar (Obrigatorio, URL ou path do arquivo PDF enviado na versao)
* `created_at`: timestamp (Obrigatorio)

### Entidade: Avaliacao (Pareceres Tecnicos)
Registra as avaliacoes e pareceres emitidos pelos avaliadores/revisores, permitindo multiplas correcoes e multiplos pareceres por submissao.
* `id`: uuid (Chave Primaria)
* `submissao_versao_id`: uuid (Chave Estrangeira para Submissao)
* `avaliador_id`: uuid (Chave Estrangeira para Usuario atuando como avaliador)
* `status_parecer`: varchar (Obrigatorio, ex: APROVADO, REJEITADO, NECESSITA_CORRECAO)
* `observacoes`: text (Obrigatorio, feedback detalhado e observacoes dos revisores para o autor)
* `pontuacao`: decimal (Opcional, nota consolidada dos criterios tecnicos)
* `created_at`: timestamp (Obrigatorio)
* `updated_at`: timestamp (Obrigatorio)

### Entidade: Local
Representa as salas, auditatorios ou espacos fisicos/virtuais onde ocorrerao as apresentacoes.
* `id`: uuid (Chave Primaria)
* `nome`: varchar (Obrigatorio)
* `descricao`: text (Opcional)
* `capacidade`: integer (Opcional)

### Entidade: Apresentacao
Representa a agenda ou alocacao da submissao aceita para apresentacao no evento.
* `id`: uuid (Chave Primaria)
* `submissao_id`: uuid (Chave Estrangeira para Submissao)
* `local_id`: uuid (Chave Estrangeira para Local)
* `inicio`: timestamp (Obrigatorio)
* `duracao_minutos`: integer (Obrigatorio)

---

## 3. Relacionamentos do Modelo (Schema Mapping)

* **Usuario (1) -> (*) Submissao** (Como autor principal)
* **Usuario (1) -> (*) SubmissaoAutor** (Vinculo de autoria/coautoria)
* **Area (1) -> (*) Submissao** (Classificacao tematica)
* **Submissao (1) -> (1) Evento** (Chave estrangeira `evento_id` para integracao com o modulo de eventos)
* **Submissao (1) -> (*) SubmissaoVersao** (Historico de versoes de arquivos enviados para correcao)
* **Submissao (1) -> (*) Avaliacao** (Multiplos pareceres tecnicos e observacoes dos avaliadores)
* **Submissao (1) -> (*) Apresentacao** (Alocacao de agenda do trabalho aceito)
* **Local (1) -> (*) Apresentacao** (Espaco fisico da apresentacao)