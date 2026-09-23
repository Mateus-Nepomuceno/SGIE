# Diagrama de Estados

## Estados do Evento

O ciclo de vida do evento passa pelos seguintes estados principais:
* **Rascunho**
* **Configuração** (Configuracao)
* **Publicado**
* **Cancelado**

---

## Fluxo e Transições de Estados

### 1. Início ➔ Rascunho
* O evento é criado e entra no estado inicial.

### 2. Rascunho ➔ Configuração
* **Ação/Gatilho:** Inserir dados obrigatórios e opcionais.

### 3. Configuração
A partir do estado de Configuração, o usuário pode realizar as seguintes transições:
* **Configuração ➔ Configuração (Auto-transição):**
  * **Ação:** Alterar Dados.
* **Configuração ➔ Publicado:**
  * **Ação:** Publicar (o evento passa por uma decisão e segue para publicado).
* **Configuração ➔ Cancelado:**
  * **Ação:** Cancelar (o evento passa por uma decisão e segue para cancelado).

### 4. Publicado
Quando o evento está no estado Publicado, as seguintes ações e transições são permitidas sob regras de prazo:
* **Publicado ➔ Publicado (Auto-transição):**
  * **Ação:** Alterar Dados.
  * **Regras de Prazo:** 
    * 1 semana antes.
    * 1 hora antes.
* **Publicado ➔ Cancelado:**
  * **Ação:** Cancelar.
  * **Regras de Prazo:**
    * 1 semana antes.
    * 1 hora antes.

### 5. Finalização ➔ [Fim]
O diagrama aponta para o estado final a partir de:
* **Publicado:** O evento segue seu ciclo normal até ser concluído.
* **Cancelado:** O ciclo de vida do evento é encerrado de forma prematura.