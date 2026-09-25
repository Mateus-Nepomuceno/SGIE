# Documento de Requisitos do Sistema

## Requisitos Funcionais

### \[RFS01\] Realização de Inscrição em Evento
**Atores:** Participante
Esse requisito permite que um usuário autenticado se inscreva escolhendo categoria e anexando comprovante se necessário. Para realizar uma inscrição em um evento, o participante deve possuir cadastro no sistema. Os dados cadastrados (provenientes do módulo de Usuários) serão utilizados automaticamente no preenchimento da inscrição. Se o evento for pago, aciona o módulo de Pagamentos (mas não processa a cobrança).

| Nome do campo | Descrição do campo |
| :--- | :--- |
| **\*ID do usuário** | Identificador do participante, obtido automaticamente do módulo de Usuários após autenticação. |
| **\*ID do evento** | Identificador do evento no qual a inscrição está sendo realizada. |
| **\*Categoria de participante** | Categoria escolhida pelo usuário (por exemplo: estudante, profissional, convidado), entre as definidas pelo evento. |
| **Comprovante de categoria** | Documento anexado pelo participante, exigido apenas quando a categoria escolhida requer comprovação. |
| **Dados Adicionais** | Campos extras que o organizador do evento eventualmente exige. |

*(\*) campos de preenchimento obrigatório*
**Prioridade:** \[X\] Essencial \[ \] Média \[ \] Baixa

---

### \[RFS02\] Definição de Situação da Inscrição
**Atores:** Organizador
O sistema continua responsável por atualizar automaticamente situações como confirmação, mas "Sistema" não aparece como ator. O requisito já descreve essas atualizações como comportamento do sistema.

| Situação | Descrição |
| :--- | :--- |
| **Pendente** | Situação inicial da inscrição, enquanto o preenchimento ou alguma etapa necessária ainda não foi concluída. |
| **Pendente de validação** | A inscrição aguarda a análise de um comprovante exigido pela categoria escolhida. |
| **Confirmada** | A inscrição foi concluída e está apta a participar do evento. |
| **Em lista de espera** | Não há vaga disponível no momento; a inscrição aguarda a liberação de uma vaga. |
| **Cancelada** | Inscrição cancelada pelo participante ou por um organizador. |

**Prioridade:** \[X\] Essencial \[ \] Média \[ \] Baixa

---

### \[RFS03\] Controle do Limite de Vagas
**Atores:** Participante
O controle acontece automaticamente quando o participante tenta realizar uma nova inscrição; o requisito diz que a verificação ocorre “antes de cada nova inscrição”.

| Nome do campo | Descrição do campo |
| :--- | :--- |
| **\*ID do Evento** | Referência ao evento cuja disponibilidade está sendo verificada. |
| **\*Capacidade Máxima** | Limite de vagas do evento, obtido do módulo de Eventos. |
| **\*Vagas Ocupadas** | Número de inscrições ativas contabilizadas para o evento. |
| **Vagas Disponíveis** | Calculado como Capacidade Máxima − Vagas Ocupadas. |

*(\*) campos de preenchimento obrigatório*
**Prioridade:** \[X\] Essencial \[ \] Média \[ \] Baixa

---

### \[RFS04\] Gerenciamento de Lista de Espera
**Atores:** Participante
A lista está vinculada ao participante que não conseguiu vaga e entra na fila. A promoção posterior é automática e permanece como comportamento do sistema.

| Nome do campo | Descrição do campo |
| :--- | :--- |
| **\*ID da Inscrição** | Referência à inscrição em lista de espera. |
| **\*Posição na Lista** | Ordem do participante na fila de espera. |
| **Data de Entrada** | Data/hora em que entrou na lista de espera. |

*(\*) campos de preenchimento obrigatório*
**Prioridade:** \[X\] Essencial \[ \] Média \[ \] Baixa

---

### \[RFS05\] Emissão e Disponibilização de Ingresso
**Atores:** Participante
Ao confirmar a inscrição, o sistema gera automaticamente um ingresso com código único, usado depois no credenciamento.

| Nome do campo | Descrição do campo |
| :--- | :--- |
| **\*ID da Inscrição** | Referência à inscrição confirmada à qual o ingresso pertence. |
| **\*Código Único (QR Code)** | Identificador único do ingresso, apresentado em tamanho adequado para leitura no credenciamento. |
| **\*Nome do Participante** | Obtido do módulo de Usuários. |
| **\*Evento** | Nome, data e local do evento, obtidos do módulo de Eventos. |
| **Categoria de Participante** | Categoria associada à inscrição (RF01). |
| **Data de Emissão** | Registro automático do momento da geração do ingresso. |

*(\*) campos de preenchimento obrigatório*
**Prioridade:** \[X\] Essencial \[ \] Média \[ \] Baixa

---

### \[RFS06\] Consulta de Inscrições
**Atores:** Participante
O participante consulta os dados e a situação da própria inscrição.

| Nome do campo | Descrição do campo |
| :--- | :--- |
| **Busca: Evento** | Restringe a consulta a um evento específico. |
| **Filtro: Situação** | Restringe pela situação atual da inscrição (RF02). |
| **Filtro: Categoria** | Restringe pela categoria de participante. |
| **Resultado** | Dados da inscrição e sua situação atual. |

**Prioridade:** \[X\] Essencial \[ \] Média \[ \] Baixa

---

### \[RFS07\] Consulta de Participantes
**Atores:** Organizador
O organizador consulta a lista de inscritos de seus eventos, com filtros por categoria, situação e presença.

| Nome do campo | Descrição do campo |
| :--- | :--- |
| **Filtro: Categoria** | Restringe pela categoria de participante. |
| **Filtro: Situação** | Restringe pela situação da inscrição, conforme RF02. |
| **Filtro: Presença** | Restringe por presença registrada ou não. |
| **Resultado** | Lista de participantes/inscrições com os dados relevantes de cada um. |

**Prioridade:** \[X\] Essencial \[ \] Média \[ \] Baixa

---

### \[RFS08\] Cancelamento de Inscrição
**Atores:** Participante, Organizador
O participante ou organizador pode cancelar uma inscrição, liberando a vaga correspondente quando aplicável.

| Nome do campo | Descrição do campo |
| :--- | :--- |
| **\*ID da Inscrição** | Referência à inscrição a ser cancelada. |
| **Motivo do Cancelamento** | Texto opcional informado pelo solicitante. |
| **\*Solicitante** | Indica se o cancelamento foi feito pelo participante ou por um organizador. |
| **Data do Cancelamento** | Registro automático de data/hora. |

*(\*) campos de preenchimento obrigatório*
**Prioridade:** \[X\] Essencial \[ \] Média \[ \] Baixa

---

### \[RFS09\] Gerenciamento de Presença de Participantes
**Atores:** Organizador
O organizador pode registrar a presença dos participantes no evento por meio de credenciamento. O credenciamento é opcional e pode ser realizado por leitura do código do ingresso ou manualmente pelo organizador. Somente inscrições confirmadas podem ter a presença registrada.

| Nome do campo | Descrição do campo |
| :--- | :--- |
| **\*ID da Inscrição** | Referência à inscrição confirmada. |
| **\*Código de Check-in** | Código único gerado automaticamente na confirmação da inscrição. |
| **Método de Registro** | Automático (leitura de código) ou Manual (busca por organizador). |
| **Data/Hora do Check-in** | Registro automático do momento do credenciamento. |
| **Responsável pelo Registro** | Organizador que realizou o credenciamento (sempre registrado, mesmo no método automático, pelo dispositivo/login usado). |

*(\*) campos de preenchimento obrigatório*
**Prioridade:** \[X\] Essencial \[ \] Média \[ \] Baixa

---

## Regras de Negócio

### Acesso e Identidade
* **RN01:** Só usuários autenticados podem se inscrever. Caso o participante não possua cadastro, o sistema deve direcioná-lo ao cadastro e, após sua conclusão, permitir o prosseguimento da inscrição no evento selecionado.
* **RN02:** Cada usuário só pode ter uma inscrição ativa por evento.

### Categoria de Participante
* **RN03:** Toda inscrição tem uma categoria, escolhida entre as que o evento configurou. Se a categoria exigir comprovante, a inscrição fica "pendente de validação" até um organizador aprovar; se for rejeitado, a inscrição é cancelada e o participante é avisado.
* **RN04:** A categoria pode influenciar o valor cobrado, mas quem calcula esse valor é o módulo de Pagamentos.

### Situação da Inscrição
* **RN05:** Toda inscrição começa "pendente" e só muda de situação por causa de um evento concreto (pagamento aprovado, comprovante validado, vaga liberada) ou de uma ação explícita, como cancelamento.
* **RN06:** A inscrição fica "confirmada" de acordo com a combinação entre o tipo de evento e a categoria escolhida, mas em todos os casos a confirmação depende também de que o participante tenha preenchido todos os dados exigidos na inscrição (RFS01), dentro do prazo de reserva estabelecido na RN11. Se o prazo expirar antes disso, a inscrição não chega a ser confirmada e é cancelada automaticamente.
  * *Evento gratuito, categoria sem exigência de comprovante:* a inscrição é confirmada assim que é criada.
  * *Evento gratuito, categoria com exigência de comprovante:* a inscrição é confirmada quando o comprovante é aprovado por um organizador.
  * *Evento pago, categoria sem exigência de comprovante:* a inscrição é confirmada quando o pagamento, realizado durante o processo de inscrição, é aprovado pelo módulo de Pagamentos. Caso o pagamento não seja aprovado, a inscrição não é confirmada e é cancelada automaticamente.
  * *Evento pago, categoria com exigência de comprovante:* a inscrição é confirmada somente quando o comprovante é aprovado e o pagamento, realizado durante o processo de inscrição, também é aprovado, nessa ordem ou em paralelo. Caso o pagamento não seja aprovado, a inscrição não é confirmada e é cancelada automaticamente.
* **RN07:** Em eventos pagos, o pagamento é realizado durante o processo de inscrição e processado pelo módulo de Pagamentos. A inscrição será confirmada após a aprovação do pagamento e, quando aplicável, da validação do comprovante de categoria.
* **RN08:** A inscrição pode ser cancelada a partir de qualquer situação ativa ("pendente", "pendente de validação", "em lista de espera" ou "confirmada"). Uma vez cancelada, não muda mais.
* **RN09:** Toda mudança de situação é registrada com data e hora.

### Controle de Vagas e Lista de Espera
* **RN10:** Antes de criar uma inscrição, o sistema verifica se há vaga disponível. Contam como vaga ocupada todas as inscrições em situação ativa; canceladas não contam. *(Nota: Corrigido de RN010 para RN10 para manter o padrão)*
* **RN11:** Toda inscrição não confirmada ocupa a vaga por tempo limitado. Na situação “pendente”, o participante possui um prazo para concluir o preenchimento das informações exigidas. Caso o prazo expire, a inscrição é cancelada automaticamente e a vaga é liberada.
* **RN12:** A capacidade máxima do evento vem do módulo de Eventos; este módulo apenas consome esse dado. Eventos sem capacidade definida não têm controle de vagas nem lista de espera.
* **RN13:** Sem vaga disponível, a inscrição vai automaticamente para a lista de espera, em ordem de chegada. Quando uma vaga é liberada, o próximo da fila é promovido, com o mesmo prazo de reserva da RN11. O participante também pode desistir da lista de espera a qualquer momento, com efeito equivalente a um cancelamento.

### Cancelamento
* **RN14:** O cancelamento pode ser feito pelo próprio participante ou por um organizador, nesse caso com justificativa registrada, a partir de qualquer situação ativa da inscrição.
* **RN15:** Cancelar uma inscrição confirmada libera a vaga, promove o próximo da lista de espera e invalida o ingresso emitido. Em evento pago, o sistema aciona o fluxo de reembolso junto ao módulo de Pagamentos.
* **RN16:** Uma inscrição cancelada não pode ser reativada; um novo interesse do participante exige uma nova inscrição.

### Ingresso
* **RN17:** O ingresso só deve ser gerado automaticamente quando a inscrição estiver com situação "confirmada".
* **RN18:** Cada ingresso deve possuir um código único (QR Code) associado exclusivamente à inscrição confirmada, sendo utilizado para validação no credenciamento.
* **RN19:** O QR Code deverá ser dimensionado e apresentado de forma a permitir leitura rápida pelo dispositivo de credenciamento na distância operacional definida para o evento, considerando resolução da câmera, iluminação e tamanho dos módulos do código.
* **RN20:** O ingresso deve apresentar os dados da inscrição e do evento, incluindo nome do participante, evento, data, local e categoria, obtidos dos respectivos módulos do sistema.

### Presença e Credenciamento
* **RN21:** Somente inscrições com situação "confirmada" podem realizar o credenciamento e ter a presença registrada.
* **RN22:** O credenciamento pode ser realizado por leitura do código do ingresso ou manualmente pelo organizador, por meio da busca da inscrição.
* **RN23:** Ao realizar o credenciamento, o sistema deve registrar automaticamente a data e hora, o método utilizado e o organizador responsável pelo registro, inclusive quando a leitura do código for automática.

### Consultas
* **RN24:** O participante só pode consultar suas próprias inscrições, visualizando os dados e a situação atual de cada inscrição.
* **RN25:** O organizador só pode consultar os participantes inscritos nos eventos sob sua responsabilidade, podendo filtrar os resultados por categoria, situação da inscrição e presença.
* **RN26:** Os resultados das consultas devem refletir a situação e a presença registradas no sistema no momento da consulta, apresentando os dados relevantes de cada inscrição ou participante.
