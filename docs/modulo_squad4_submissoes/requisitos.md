# DOCUMENTO DE ESPECIFICACAO TECNICA: MODULO DE SUBMISSAO DE TRABALHOS ACADEMICOS

## 1. VISAO GERAL DO MODULO
Este documento detalha o funcionamento tecnico, a estrutura de dados e o fluxo operacional do Modulo de Submissao. O objetivo e gerenciar o ciclo de vida completo de trabalhos academicos em eventos cientificos, desde o rascunho inicial pelo autor ate a decisao final (avaliacao, curadoria, pareces e comunicacao), integrando-se estritamente com os modulos externos de Usuarios, Eventos e Inscricoes.

---

## 2. FLUXO OPERACIONAL PASSO A PASSO

### 2.1. Validacao de Vinculos e Permissoes (Integracao Externa)
* Objetivo: Garantir que apenas usuarios aptos interajam com o sistema (RF09).
* Fluxo:
  1. O usuario tenta acessar o modulo de submissao.
  2. O sistema consulta o Modulo de Usuarios para validar o cadastro e o perfil do usuario.
  3. O sistema consulta o Modulo de Inscricoes para verificar se o usuario possui inscricao ativa no evento correspondente (recebendo o ID do Evento como chave estrangeira).
* Regra: Caso o usuario nao esteja cadastrado ou nao tenha inscricao ativa, o acesso para submissao ou atuacao como avaliador e bloqueado.

### 2.2. Configuracao de Tipos, Areas e Prazos (Configuracao Previa)
* Objetivo: Definir a estrutura aceita pelo evento.
* Fluxo:
  1. O administrador define as modalidades ou tipos de trabalho e as areas tematicas validas.
  2. O sistema estipula as datas de inicio e fim do periodo de submissao (RF03).
* Regra: O envio de trabalhos so e liberado se a data atual estiver estritamente dentro do periodo configurado.

### 2.3. Cadastro, Perfis Acadêmicos e Submissao pelo Autor
* Objetivo: Permitir o registro do trabalho academico, perfis complementares e seus respectivos autores (RF01, RF02, RF10).
* Fluxo:
  1. O autor principal inicia o cadastro do trabalho, que e salvo inicialmente no estado de rascunho (RF04).
  2. O autor vincula obrigatoriamente uma modalidade e uma area tematica valida.
  3. O sistema cadastra o autor principal e identifica os coautores necessarios para fins de certificacao posterior.
  4. **Adicao de Campos Obrigatorios de Perfil:** No cadastro do autor principal e coautores, o sistema deve coletar e validar campos complementares essenciais para auditoria e curadoria academica:
     * Link do Curriculo Lattes (Validacao de URL).
     * Perfil do LinkedIn (Validacao de URL).
     * Afiliação Institucional e Maior Titulação.
  5. Ao finalizar o preenchimento, anexar o documento PDF/DOCX compativel com o formato exigido e submeter dentro do prazo valido, o estado do trabalho muda de rascunho para submetida (RF04).

### 2.4. Distribuicao dos Trabalhos para Avaliadores
* Objetivo: Alocar os artigos submetidos aos revisores qualificados (RF05).
* Fluxo:
  1. Com base na area tematica do trabalho, o sistema filtra os avaliadores disponiveis e elegiveis, aplicando regras de prevencao de conflito de interesse.
  2. Os trabalhos submetidos sao distribuidos aos avaliadores respeitando os criterios de alocacao definidos.
  3. O estado do trabalho transita para em avaliacao (RF04).

### 2.5. Avaliacao Tecnica e Emissao de Pareceres
* Objetivo: Registrar o feedback, pontuacao e pareceres tecnicos dos revisores (RF06).
* Fluxo:
  1. O avaliador acessa o trabalho atribuido e preenche os criterios tecnicos estabelecidos no sistema.
  2. O sistema registra o parecer tecnico individual de cada revisor, contendo notas por criterio e justificativas textuais obrigatorias.

### 2.6. Curadoria, Ciclo de Ajustes e Decisao Final
* Objetivo: Consolidar as avaliações, gerenciar o fluxo de correções e definir o resultado final da submissão (RF07, RF08).
* Fluxo:
  1. Com base nos pareceres consolidados dos revisores, o comitê ou o sistema registra uma das seguintes decisões de curadoria (RF04, RF07):
     * **Aceita:** O trabalho atende a todos os requisitos e segue para publicação.
     * **Rejeitada:** O trabalho não atinge os critérios de qualidade do evento.
     * **Correções Solicitadas (Retorno para Correção):** O trabalho necessita de ajustes menores ou maiores apontados pelos revisores.
  2. **Regra de Retorno para Correção:** Sempre que o trabalho for retornado para correção, o sistema exige o preenchimento obrigatório de **observações detalhadas** por parte dos avaliadores/editores. O trabalho muda para o estado de correções solicitadas, abrindo um prazo limite para que o autor principal substitua o arquivo do artigo e envie uma nova versão para nova rodada de revisão.
  3. Assim que a decisão final for consolidada (Aceita ou Rejeitada), o sistema dispara uma notificação formal para o autor principal.

---

## 3. RESUMO DE INTEGRACOES E DADOS

### 3.1. Dados Recebidos de Outros Modulos
* ID do Evento (Chave estrangeira).
* Dados cadastrais de usuarios (Autores e Avaliadores).
* Status de confirmacao de inscricao.

### 3.2. Dados Fornecidos para Outros Modulos
* Status atualizado da submissao (Rascunho, Submetida, Em avaliacao, Correcoes solicitadas, Aceita, Rejeitada).
* Pareceres detalhados dos avaliadores e resultado final para fins de consulta, auditoria e emissao de certificados.

---

## 4. ESPECIFICACAO FORMAL DOS REQUISITOS FUNCIONAIS (RF)

### RF01 - Cadastro de Tipos e Areas
* Descricao: O sistema deve permitir a definicao de tipos/modalidades de trabalho e areas tematicas.
* Regra de Negocio: Cada trabalho submetido deve estar vinculado obrigatoriamente a uma modalidade e a uma area tematica valida.

### RF02 - Modelagem de Submissao, Autoria e Perfis Profissionais
* Descricao: O sistema deve permitir o cadastro de trabalhos academicos, incluindo seus autores e coautores.
* Regra de Negocio: As submissoes sao opcionais para os eventos. Deve haver a identificacao correta do autor principal e coautores. O cadastro obrigatorio deve exigir dados complementares como **Link do Curriculo Lattes**, **Perfil do LinkedIn** e **Afiliacao Institucional**.

### RF03 - Periodo de Submissao
* Descricao: O sistema deve permitir a definicao de um periodo especifico de submissao.
* Regra de Negocio: O envio de trabalhos so pode ser realizado dentro das datas de inicio e fim estipuladas para o evento.

### RF04 - Gestao Avancada de Estados da Submissao
* Descricao: O sistema deve gerenciar o ciclo de vida do trabalho atraves dos estados: rascunho, submetida, em avaliacao, correcoes solicitadas, aceita e rejeitada.
* Regra de Negocio: Uma submissao iniciada fica como rascunho ate ser finalizada. Apos o envio, transita para submetida, passando pelo fluxo de avaliacao, podendo retornar para correcoes com observacoes obrigatorias antes da decisao final.

### RF05 - Distribuicao de Trabalhos
* Descricao: O sistema deve permitir a distribuicao dos trabalhos submetidos para os avaliadores.
* Regra de Negocio: A atribuicao de avaliadores deve respeitar a area tematica do trabalho e criterios de distribuicao, evitando conflitos de interesse institucionais.

### RF06 - Avaliacao e Criterios Tecnicos
* Descricao: O sistema deve permitir a definicao de criterios e o registro da avaliacao feita pelos revisores.
* Regra de Negocio: Cada avaliador deve preencher os criterios estabelecidos para gerar um parecer tecnico estruturado.

### RF07 - Curadoria, Parecer e Decisao Final
* Descricao: O sistema deve consolidar o parecer e registrar a decisao final sobre a submissao.
* Regra de Negocio: A decisao final baseia-se nas avaliacoes consolidadas dos revisores, podendo resultar em aceitacao, rejeicao ou retorno para correcao com observacoes obrigatorias.

### RF08 - Comunicacao de Resultados
* Descricao: O sistema deve definir como os resultados das avaliacoes serao comunicados aos autores.
* Regra de Negocio: O autor principal deve ser notificado formalmente por e-mail ou painel assim que a decisao final ou solicitacao de ajuste for registrada no modulo.

### RF09 - Identificacao de Dependencias Externas
* Descricao: O sistema deve se comunicar com os modulos de Usuarios, Eventos e Inscricoes para validar permissoes e vinculos.
* Regra de Negocio: Apenas usuarios devidamente cadastrados e com inscricao ativa no evento podem submeter trabalhos ou atuar como avaliadores.

### RF10 - Gestao de Autores, Coautores e Historico de Arquivos
* Descricao: O sistema deve permitir vincular multiplos autores a uma submissao e gerenciar o versionamento de arquivos.
* Regra de Negocio: O autor principal gerencia o envio principal e as re-submissoes solicitadas no fluxo de curadoria, mantendo rastreabilidade das versoes enviadas.