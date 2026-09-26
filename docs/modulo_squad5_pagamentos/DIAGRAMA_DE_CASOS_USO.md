# Diagrama de Casos de Uso

O documento a seguir detalha a estrutura de interações dos usuários e sistemas representados no arquivo diagrama de casos de uso.jpg. 

*Nota: Os rótulos de texto dos atores originais não são visíveis na imagem. Foram inferidos nomes descritivos com base nas ações que cada perfil executa.*

## Diagrama Visual (Mermaid)

```mermaid
flowchart LR
    %% Definição de Atores (Nomes inferidos)
    Admin((Administrador))
    Gateway((Gateway de\nPagamento))
    Participante((Participante))
    Financeiro((Sistema\nFinanceiro))

    %% Casos de Uso
    UC1([Acessar Dashboard Administrativo])
    UC2([Gerenciar Categorias de Preço e Lotes])
    UC3([Gerar Relatórios Financeiros])
    UC4([Registrar Isenção ou Abatimento])
    UC5([Emitir / Disponibilizar Certificados])
    UC6([Enviar Comunicações Pós-evento])
    UC7([Processar Pagamento])
    UC8([Realizar Pagamento da Inscrição])
    UC9([Consultar Status do Pagamento])
    UC10([Solicitar Reembolso])
    UC11([Acessar Certificado])
    UC12([Gerar Cobrança])
    UC13([Gerenciar Reembolso])

    %% Relacionamentos Ator -> Caso de Uso
    Admin --- UC1
    Admin --- UC2
    Admin --- UC3
    Admin --- UC4
    Admin --- UC5
    Admin --- UC6

    Gateway --- UC7

    Participante --- UC8
    Participante --- UC9
    Participante --- UC10
    Participante --- UC11

    Financeiro --- UC12
    Financeiro --- UC13

    %% Relacionamentos de Inclusão/Extensão
    UC8 -. "<<include>>" .-> UC7

    %% Notas Explicativas
    Nota1["A cobrança é gerada quando uma\nInscrição exige pagamento.\n\nO valor considera a categoria\ne o lote aplicáveis."]
    Nota2["A emissão/disponibilização depende\ndos dados de inscrição e da\npresença confirmada.\n\nO registro de presença pertence\nao fluxo de Inscrições/Participantes."]
    Nota3["O processamento é realizado\npor meio do Gateway de Pagamento.\n\nO resultado atualiza a situação\nfinanceira da inscrição."]

    %% Vínculo das notas com os Casos de Uso
    UC12 -.- Nota1
    UC5 -.- Nota2
    UC7 -.- Nota3

    %% Estilização
    classDef actor fill:transparent,stroke:transparent,font-weight:bold;
    class Admin,Gateway,Participante,Financeiro actor;
    classDef note fill:#FFF9C4,stroke:#333,stroke-width:1px,color:#000,text-align:left;
    class Nota1,Nota2,Nota3 note;
```

## Atores (Inferidos)

1. **Administrador (ou Organizador):** Responsável por configurações globais, gestão financeira e disparos de pós-evento.
2. **Gateway de Pagamento (ou Sistema Externo):** Responsável pela efetivação técnica da transação financeira.
3. **Participante (ou Inscrito):** O usuário final que realiza os pagamentos e consome o resultado da inscrição (status, certificado, etc).
4. **Sistema Financeiro (ou Módulo Interno):** Responsável pela geração primária da fatura e acompanhamento do ciclo de vida dos valores (cobrança e reembolso).

## Relacionamentos Principais

### Administrador
* Acessar Dashboard Administrativo
* Gerenciar Categorias de Preço e Lotes
* Gerar Relatórios Financeiros
* Registrar Isenção ou Abatimento
* Emitir / Disponibilizar Certificados
* Enviar Comunicações Pós-evento

### Gateway de Pagamento
* Processar Pagamento

### Participante
* Realizar Pagamento da Inscrição
* Consultar Status do Pagamento
* Solicitar Reembolso
* Acessar Certificado

### Sistema Financeiro
* Gerar Cobrança
* Gerenciar Reembolso

## Relacionamentos Especiais (Include)

* O caso de uso **Realizar Pagamento da Inscrição** inclui obrigatoriamente (`<<include>>`) a execução do caso de uso **Processar Pagamento**.

## Notas e Regras de Negócio

Conforme destacado nos quadros amarelos do diagrama original, as seguintes regras são aplicadas:

1. **Sobre a Geração de Cobrança (Referente a "Gerar Cobrança"):**
   * A cobrança é gerada quando uma Inscrição exige pagamento.
   * O valor considera a categoria e o lote aplicáveis.

2. **Sobre Certificados (Referente a "Emitir / Disponibilizar Certificados"):**
   * A emissão/disponibilização depende dos dados de inscrição e da presença confirmada.
   * O registro de presença pertence ao fluxo de Inscrições/Participantes.

3. **Sobre o Processamento (Referente a "Processar Pagamento"):**
   * O processamento é realizado por meio do Gateway de Pagamento.
   * O resultado atualiza a situação financeira da inscrição.