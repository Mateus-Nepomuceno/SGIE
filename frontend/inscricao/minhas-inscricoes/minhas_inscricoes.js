let todasInscricoes = [];
let filtroStatusAtivo = '';

const STATUS_CONFIG = {
    confirmada: {
        texto: 'Confirmada',
        artigoClass: 'minhas-inscricoes__article-item-1-confirmada',
        badgeClass: 'minhas-inscricoes__background-border',
        badgeTextoClass: 'minhas-inscricoes__text-20',
        badgeIcon: `
            <svg viewBox="0 0 13.333 13.333" xmlns="http://www.w3.org/2000/svg" fill="none" class="minhas-inscricoes__icon-12" role="img">
              <path d="M5.733 9.733 L10.433 5.033 L9.5 4.1 L5.733 7.867 L3.833 5.967 L2.9 6.9 L5.733 9.733 Z" fill="rgb(6, 95, 70)" />
            </svg>
        `
    },
    pendente_pagamento: {
        texto: 'Pendente de Pagamento',
        artigoClass: 'minhas-inscricoes__article-item-2-pendente-de-pagamento',
        badgeClass: 'minhas-inscricoes__background-border-2',
        badgeTextoClass: 'minhas-inscricoes__text-30',
        badgeIcon: `
            <svg viewBox="0 0 13.333 13.333" xmlns="http://www.w3.org/2000/svg" fill="none" class="minhas-inscricoes__icon-17" role="img">
              <path d="M6.667 0 C2.987 0 0 2.987 0 6.667 C0 10.347 2.987 13.333 6.667 13.333 C10.347 13.333 13.333 10.347 13.333 6.667 C13.333 2.987 10.347 0 6.667 0 Z M6.667 12 C3.727 12 1.333 9.607 1.333 6.667 C1.333 3.727 3.727 1.333 6.667 1.333 C9.607 1.333 12 3.727 12 6.667 C12 9.607 9.607 12 6.667 12 Z M7 3.333 L6 3.333 L6 7.333 L9.5 9.433 L10 8.6 L7 6.833 Z" fill="rgb(133, 83, 0)" />
            </svg>
        `
    },
    lista_espera: {
        texto: 'Lista de Espera',
        artigoClass: 'minhas-inscricoes__article-item-3-lista-de-espera',
        badgeClass: 'minhas-inscricoes__background-border-3',
        badgeTextoClass: 'minhas-inscricoes__text-40',
        badgeIcon: `
            <svg viewBox="0 0 10.667 13.333" xmlns="http://www.w3.org/2000/svg" fill="none" class="minhas-inscricoes__icon-21" role="img">
              <path d="M2.667 12 L8 12 L8 10 C8 9.267 7.733 8.64 7.213 8.12 C6.693 7.6 6.067 7.333 5.333 7.333 C4.6 7.333 3.973 7.6 3.453 8.12 C2.933 8.64 2.667 9.267 2.667 10 Z" fill="rgb(0, 109, 65)" />
            </svg>
        `
    },
    cancelada: {
        texto: 'Cancelada',
        artigoClass: 'minhas-inscricoes__article-item-4-cancelada',
        badgeClass: 'minhas-inscricoes__background-border-4',
        badgeTextoClass: 'minhas-inscricoes__text-50',
        badgeIcon: `
            <svg viewBox="0 0 13.333 13.333" xmlns="http://www.w3.org/2000/svg" fill="none" class="minhas-inscricoes__icon-26" role="img">
              <path d="M4.267 10 L6.667 7.6 L9.067 10 L10 9.067 L7.6 6.667 L10 4.267 L9.067 3.333 L6.667 5.733 L4.267 3.333 L3.333 4.267 L5.733 6.667 L3.333 9.067 Z" fill="rgb(159, 18, 57)" />
            </svg>
        `
    }
};

document.addEventListener('DOMContentLoaded', () => {
    if (!isAuthenticated()) {
        window.location.href = resolveAppUrl('usuarios/login/login.html');
        return;
    }

    atualizarCabecalhoUsuario('minhas-inscricoes');

    const btnAplicar = document.getElementById('btn-aplicar-filtros');
    if (btnAplicar) btnAplicar.addEventListener('click', () => aplicarFiltrosLocais());

    const btnLimpar = document.getElementById('btn-limpar-filtros');
    if (btnLimpar) btnLimpar.addEventListener('click', () => {
        const inputBusca = document.getElementById('filtro-busca');
        const selectStatus = document.getElementById('filtro-status');
        if (inputBusca) inputBusca.value = '';
        if (selectStatus) selectStatus.value = '';
        filtroStatusAtivo = '';
        renderizarInscricoes(todasInscricoes);
    });

    const inputBusca = document.getElementById('filtro-busca');
    if (inputBusca) {
        inputBusca.addEventListener('keyup', (e) => {
            if (e.key === 'Enter') aplicarFiltrosLocais();
        });
    }

    const selectStatus = document.getElementById('filtro-status');
    if (selectStatus) {
        selectStatus.addEventListener('change', () => aplicarFiltrosLocais());
    }

    const btnFechar = document.getElementById('btn-fechar-ingresso');
    if (btnFechar) btnFechar.addEventListener('click', fecharIngresso);

    const overlay = document.getElementById('overlay-ingresso');
    if (overlay) {
        overlay.addEventListener('click', (e) => {
            if (e.target.id === 'overlay-ingresso') fecharIngresso();
        });
    }

    // Vincula clique nos cards de contadores
    configurarCliquesStats();

    carregarInscricoes();
});

function configurarCliquesStats() {
    const cardConfirmadas = document.getElementById('card-stat-confirmadas');
    if (cardConfirmadas) cardConfirmadas.onclick = () => alternarFiltroPorStat('confirmada');

    const cardPendentes = document.getElementById('card-stat-pendentes');
    if (cardPendentes) cardPendentes.onclick = () => alternarFiltroPorStat('pendente_pagamento');

    const cardEspera = document.getElementById('card-stat-espera');
    if (cardEspera) cardEspera.onclick = () => alternarFiltroPorStat('lista_espera');

    const cardCanceladas = document.getElementById('card-stat-canceladas');
    if (cardCanceladas) cardCanceladas.onclick = () => alternarFiltroPorStat('cancelada');
}

function alternarFiltroPorStat(status) {
    const selectStatus = document.getElementById('filtro-status');
    if (filtroStatusAtivo === status) {
        filtroStatusAtivo = '';
        if (selectStatus) selectStatus.value = '';
    } else {
        filtroStatusAtivo = status;
        if (selectStatus) selectStatus.value = status;
    }
    aplicarFiltrosLocais();
}

async function carregarInscricoes() {
    clearAlert('mensagem-alerta');
    const spinner = document.getElementById('loading-spinner');
    const lista = document.getElementById('lista-inscricoes');
    const vazio = document.getElementById('sem-inscricoes');

    if (spinner) spinner.style.display = 'block';
    if (lista) lista.style.display = 'none';
    if (vazio) vazio.style.display = 'none';

    try {
        const response = await apiFetch('/inscricoes/minhas/');
        if (spinner) spinner.style.display = 'none';

        if (response.ok) {
            todasInscricoes = await response.json();
            atualizarContadores(todasInscricoes);
            renderizarInscricoes(todasInscricoes);
        } else {
            const err = await response.json().catch(() => ({}));
            showAlert('mensagem-alerta', err.detail || 'Não foi possível carregar suas inscrições.', 'danger');
        }
    } catch (error) {
        if (spinner) spinner.style.display = 'none';
        showAlert('mensagem-alerta', 'Erro de conexão com o servidor do SGIE.', 'danger');
    }
}

function atualizarContadores(inscricoes) {
    const counts = {
        confirmada: 0,
        pendente_pagamento: 0,
        lista_espera: 0,
        cancelada: 0
    };

    inscricoes.forEach(i => {
        if (counts[i.status] !== undefined) {
            counts[i.status]++;
        }
    });

    const elConf = document.getElementById('stat-confirmadas');
    if (elConf) elConf.textContent = counts.confirmada;

    const elPend = document.getElementById('stat-pendentes');
    if (elPend) elPend.textContent = counts.pendente_pagamento;

    const elEsp = document.getElementById('stat-lista-espera');
    if (elEsp) elEsp.textContent = counts.lista_espera;

    const elCanc = document.getElementById('stat-canceladas');
    if (elCanc) elCanc.textContent = counts.cancelada;
}

function aplicarFiltrosLocais() {
    const inputBusca = document.getElementById('filtro-busca');
    const selectStatus = document.getElementById('filtro-status');

    const termo = inputBusca ? inputBusca.value.trim().toLowerCase() : '';
    const status = selectStatus ? selectStatus.value : '';
    filtroStatusAtivo = status;

    const filtradas = todasInscricoes.filter(insc => {
        const matchStatus = !status || insc.status === status;
        const matchTermo = !termo ||
            (insc.evento_nome && insc.evento_nome.toLowerCase().includes(termo)) ||
            (insc.codigo_ingresso && insc.codigo_ingresso.toLowerCase().includes(termo)) ||
            (insc.evento_local && insc.evento_local.toLowerCase().includes(termo));
        return matchStatus && matchTermo;
    });

    renderizarInscricoes(filtradas, termo, status);
}

function renderizarInscricoes(inscricoes, busca = '', statusFiltro = '') {
    const lista = document.getElementById('lista-inscricoes');
    const vazio = document.getElementById('sem-inscricoes');

    if (!lista || !vazio) return;
    lista.innerHTML = '';

    if (!inscricoes || inscricoes.length === 0) {
        vazio.style.display = 'block';
        lista.style.display = 'none';

        const tituloVazio = document.getElementById('titulo-vazio');
        const descVazio = document.getElementById('desc-vazio');

        if (busca || statusFiltro) {
            if (tituloVazio) tituloVazio.textContent = 'Nenhuma inscrição encontrada para estes filtros';
            if (descVazio) descVazio.textContent = 'Tente redefinir a busca ou limpar os filtros aplicados.';
        } else {
            if (tituloVazio) tituloVazio.textContent = 'Você ainda não possui inscrições';
            if (descVazio) descVazio.innerHTML = `Explore os eventos acadêmicos disponíveis no SGIE na <a href="${resolveAppUrl('index.html')}" style="color: #006d41; font-weight: 700; text-decoration: underline;">página inicial</a>.`;
        }
        return;
    }

    vazio.style.display = 'none';
    lista.style.display = 'flex';

    inscricoes.forEach(insc => {
        const cfg = STATUS_CONFIG[insc.status] || {
            texto: insc.status_display || insc.status,
            artigoClass: 'minhas-inscricoes__article-item-1-confirmada',
            badgeClass: 'minhas-inscricoes__background-border',
            badgeTextoClass: 'minhas-inscricoes__text-20',
            badgeIcon: ''
        };

        const card = document.createElement('div');
        card.className = cfg.artigoClass;
        card.style.position = 'relative';

        const codigoIngresso = insc.codigo_ingresso || `#SGIE-${insc.id}`;
        const categoria = insc.evento_categoria || 'Evento';
        const dataFmt = formatarData(insc.evento_data);
        const horaFmt = formatarHora(insc.evento_hora_inicio);
        const local = insc.evento_local || 'Local a confirmar';

        let badgeExtra = '';
        if (insc.status === 'lista_espera' && insc.posicao_lista_espera) {
            badgeExtra = `<p style="font-size: 13px; color: #006d41; font-weight: 700; margin: 4px 0 0 0;">Posição na fila: ${insc.posicao_lista_espera}º lugar</p>`;
        }

        let acoesHtml = '';
        if (insc.status === 'confirmada' && insc.codigo_ingresso) {
            acoesHtml += `
                <button type="button" class="btn-acao-ingresso" onclick="abrirIngresso(${insc.id})" style="display: inline-flex; align-items: center; gap: 8px; background-color: #006d41; color: #fff; padding: 10px 16px; border-radius: 10px; font-weight: 700; font-size: 14px; cursor: pointer; border: none;">
                  <svg viewBox="0 0 13.5 13.5" xmlns="http://www.w3.org/2000/svg" fill="none" style="width: 14px; height: 14px;" role="img">
                    <path d="M7.5 13.5 L7.5 12 L9 12 L9 13.5 Z M6 12 L6 8.25 L7.5 8.25 L7.5 12 Z M0 4.5 L0 0 L4.5 0 L4.5 4.5 Z M0 13.5 L0 9 L4.5 9 L4.5 13.5 Z M9 4.5 L9 0 L13.5 0 L13.5 4.5 Z" fill="rgb(255, 255, 255)" />
                  </svg>
                  <span>Ver Ingresso</span>
                </button>
            `;
        }

        if (insc.pode_cancelar) {
            const rotuloCancelar = insc.status === 'lista_espera' ? 'Desistir da Fila' : 'Cancelar Inscrição';
            acoesHtml += `
                <button type="button" class="btn-acao-cancelar" onclick="cancelarInscricao(${insc.id})" style="display: inline-flex; align-items: center; gap: 6px; background-color: #fff; color: #ba1a1a; border: 1.5px solid #fecdd3; padding: 10px 16px; border-radius: 10px; font-weight: 700; font-size: 14px; cursor: pointer;">
                  <span>${rotuloCancelar}</span>
                </button>
            `;
        }

        acoesHtml += `
            <button type="button" class="btn-acao-detalhes" onclick="alternarDetalhes(${insc.id})" style="display: inline-flex; align-items: center; gap: 6px; background-color: #f1f5f9; color: #334155; border: 1.5px solid #cbd5e1; padding: 10px 16px; border-radius: 10px; font-weight: 600; font-size: 14px; cursor: pointer;">
              <span id="rotulo-detalhes-${insc.id}">Ver Detalhes</span>
            </button>
        `;

        card.innerHTML = `
            <div class="minhas-inscricoes__container-29" style="width: 100%;">
                <div class="minhas-inscricoes__container-30">
                    <div class="minhas-inscricoes__background-5">
                        <p class="minhas-inscricoes__text-12">${categoria}</p>
                    </div>
                    <div class="minhas-inscricoes__container-31"><p class="minhas-inscricoes__text-13">•</p></div>
                    <div class="minhas-inscricoes__container-32">
                        <p class="minhas-inscricoes__text-14">${codigoIngresso}</p>
                    </div>
                    <div class="minhas-inscricoes__container-33"><p class="minhas-inscricoes__text-15">•</p></div>
                    <div class="minhas-inscricoes__container-34">
                        <p class="minhas-inscricoes__text-16">${insc.evento_modalidade || 'Presencial'}</p>
                    </div>
                </div>

                <div class="minhas-inscricoes__heading-2">
                    <p class="minhas-inscricoes__simposio-internacional-de-inteligencia-artificia">${insc.evento_nome}</p>
                </div>

                <div class="minhas-inscricoes__container-35">
                    <div class="minhas-inscricoes__container-36">
                        <div class="minhas-inscricoes__container-37">
                            <svg viewBox="0 0 13.5 15" xmlns="http://www.w3.org/2000/svg" fill="none" class="minhas-inscricoes__icon-9" role="img">
                              <path d="M1.5 15 L12 15 L12 6 L1.5 6 Z M1.5 4.5 L12 4.5 L12 3 L1.5 3 Z" fill="rgb(0, 109, 65)" />
                            </svg>
                        </div>
                        <div class="minhas-inscricoes__container-38">
                            <p class="minhas-inscricoes__text-17">${dataFmt}</p>
                        </div>
                    </div>

                    <div class="minhas-inscricoes__container-39">
                        <div class="minhas-inscricoes__container-40">
                            <svg viewBox="0 0 15 15" xmlns="http://www.w3.org/2000/svg" fill="none" class="minhas-inscricoes__icon-10" role="img">
                              <path d="M7.5 0 C3.36 0 0 3.36 0 7.5 C0 11.64 3.36 15 7.5 15 C11.64 15 15 11.64 15 7.5 C15 3.36 11.64 0 7.5 0 Z M7.5 13.5 C4.185 13.5 1.5 10.815 1.5 7.5 C1.5 4.185 4.185 1.5 7.5 1.5 C10.815 1.5 13.5 4.185 13.5 7.5 C13.5 10.815 10.815 13.5 7.5 13.5 Z" fill="rgb(0, 109, 65)" />
                            </svg>
                        </div>
                        <div class="minhas-inscricoes__container-41">
                            <p class="minhas-inscricoes__text-18">${horaFmt}</p>
                        </div>
                    </div>

                    <div class="minhas-inscricoes__container-42">
                        <div class="minhas-inscricoes__container-43">
                            <svg viewBox="0 0 12 15" xmlns="http://www.w3.org/2000/svg" fill="none" class="minhas-inscricoes__icon-11" role="img">
                              <path d="M6 0 C2.688 0 0 2.688 0 6 C0 10.5 6 15 6 15 C6 15 12 10.5 12 6 C12 2.688 9.312 0 6 0 Z" fill="rgb(0, 109, 65)" />
                            </svg>
                        </div>
                        <div class="minhas-inscricoes__container-44">
                            <p class="minhas-inscricoes__text-19">${local}</p>
                        </div>
                    </div>
                </div>

                ${badgeExtra}

                <div id="detalhes-${insc.id}" style="display: none; margin-top: 16px; padding: 14px 16px; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;">
                    <p style="margin: 0 0 6px 0; font-size: 13px; color: #475569;"><strong>Data da inscrição:</strong> ${formatarDataHora(insc.data_inscricao)}</p>
                    <p style="margin: 0 0 6px 0; font-size: 13px; color: #475569;"><strong>Valor:</strong> ${insc.evento_e_gratuito ? 'Gratuito' : formatarMoeda(insc.evento_preco)}</p>
                    <p style="margin: 0 0 6px 0; font-size: 13px; color: #475569;"><strong>Campos adicionais informados:</strong> ${formatarDadosAdicionais(insc.dados_adicionais)}</p>
                    ${insc.comprovante ? `<p style="margin: 0; font-size: 13px;"><a href="${insc.comprovante}" target="_blank" rel="noopener noreferrer" style="color: #006d41; font-weight: 700; text-decoration: underline;">Visualizar comprovante enviado</a></p>` : ''}
                </div>
            </div>

            <div class="minhas-inscricoes__container-45" style="display: flex; flex-direction: column; align-items: flex-end; gap: 12px;">
                <div class="${cfg.badgeClass}">
                    <div class="minhas-inscricoes__container-46">
                        ${cfg.badgeIcon}
                    </div>
                    <p class="${cfg.badgeTextoClass}">${insc.status_display || cfg.texto}</p>
                </div>

                <div style="display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end;">
                    ${acoesHtml}
                </div>
            </div>
        `;

        lista.appendChild(card);
    });
}

function formatarDadosAdicionais(dados) {
    if (!dados) return 'Nenhum';
    if (typeof dados === 'string') {
        try {
            const parsed = JSON.parse(dados);
            return formatarDadosAdicionais(parsed);
        } catch {
            return dados.trim() || 'Nenhum';
        }
    }
    if (typeof dados === 'object') {
        const entradas = Object.entries(dados).filter(([, v]) => v !== null && v !== undefined && v !== '');
        if (entradas.length === 0) return 'Nenhum';
        return entradas.map(([campo, valor]) => `${campo}: ${valor}`).join(' · ');
    }
    return String(dados);
}

function alternarDetalhes(id) {
    const el = document.getElementById(`detalhes-${id}`);
    const rotulo = document.getElementById(`rotulo-detalhes-${id}`);
    if (!el) return;
    const estaVisivel = el.style.display !== 'none';
    el.style.display = estaVisivel ? 'none' : 'block';
    if (rotulo) rotulo.textContent = estaVisivel ? 'Ver Detalhes' : 'Ocultar Detalhes';
}

async function cancelarInscricao(id) {
    const insc = todasInscricoes.find(i => i.id === id);
    const mensagem = insc && insc.status === 'lista_espera'
        ? 'Deseja realmente desistir da lista de espera deste evento?'
        : 'Deseja realmente cancelar esta inscrição? Esta ação liberará a vaga para outros participantes.';

    if (!window.confirm(mensagem)) return;

    try {
        const res = await apiFetch(`/inscricoes/${id}/`, { method: 'DELETE' });

        if (res.ok || res.status === 204) {
            showAlert('mensagem-alerta', 'Inscrição cancelada com sucesso.', 'success');
            carregarInscricoes();
        } else {
            const err = await res.json().catch(() => ({}));
            showAlert('mensagem-alerta', err.detail || 'Não foi possível cancelar a inscrição.', 'danger');
        }
    } catch (error) {
        showAlert('mensagem-alerta', 'Erro de comunicação ao cancelar inscrição.', 'danger');
    }
}

function abrirIngresso(id) {
    const insc = todasInscricoes.find(i => i.id === id);
    if (!insc || !insc.codigo_ingresso) return;

    const user = getUser();
    const nomeParticipante = user ? (user.nome_completo || user.email) : 'Participante';
    const qrData = encodeURIComponent(insc.codigo_ingresso);
    const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${qrData}`;

    const conteudo = document.getElementById('conteudo-ingresso');
    if (!conteudo) return;

    conteudo.innerHTML = `
        <div class="ticket-imprimivel" id="ticket-imprimivel" style="text-align: center; padding: 24px; background: #ffffff; border-radius: 16px;">
            <span style="display: inline-block; padding: 4px 12px; background-color: #ecfdf5; color: #006d41; border-radius: 20px; font-size: 12px; font-weight: 700; margin-bottom: 12px;">INGRESSO DIGITAL OFICIAL</span>
            <h2 style="font-size: 20px; font-weight: 800; color: #0f172a; margin: 0 0 8px 0;">${insc.evento_nome}</h2>
            <p style="font-size: 14px; color: #475569; margin: 0 0 16px 0;">${formatarData(insc.evento_data)} às ${formatarHora(insc.evento_hora_inicio)} • ${insc.evento_local}</p>
            
            <div style="display: inline-block; padding: 12px; background: #ffffff; border: 2px dashed #cbd5e1; border-radius: 12px; margin-bottom: 16px;">
                <img src="${qrUrl}" alt="QR Code do ingresso" style="width: 180px; height: 180px; display: block; margin: 0 auto;">
            </div>

            <p style="font-family: monospace; font-size: 18px; font-weight: 800; letter-spacing: 1px; color: #006d41; margin: 0 0 6px 0;">${insc.codigo_ingresso}</p>
            <p style="font-size: 15px; font-weight: 700; color: #0f172a; margin: 0 0 4px 0;">${nomeParticipante}</p>
            <p style="font-size: 13px; color: #64748b; margin: 0;">Apresente este QR Code ou informe o código no credenciamento do evento.</p>
        </div>
        <div style="display: flex; gap: 12px; justify-content: center; margin-top: 16px; border-top: 1px solid #f1f5f9; padding-top: 16px;">
            <button type="button" class="btn btn-primary" onclick="window.print()" style="padding: 10px 20px; font-weight: 700; border-radius: 10px; background-color: #006d41; color: #fff; border: none; cursor: pointer;">Imprimir Ingresso</button>
            <button type="button" class="btn btn-outline" onclick="fecharIngresso()" style="padding: 10px 20px; font-weight: 700; border-radius: 10px; background-color: #f1f5f9; color: #334155; border: 1.5px solid #cbd5e1; cursor: pointer;">Fechar</button>
        </div>
    `;

    const overlay = document.getElementById('overlay-ingresso');
    if (overlay) overlay.style.display = 'flex';
}

function fecharIngresso() {
    const overlay = document.getElementById('overlay-ingresso');
    if (overlay) overlay.style.display = 'none';
}
