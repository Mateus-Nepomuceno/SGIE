let todosParticipantes = [];
let eventoSelecionadoId = null;

const STATUS_CONFIG_PARTICIPANTE = {
    confirmada: {
        texto: 'Confirmada',
        artigoClass: 'consulta-de-participantes__article-item-1-confirmada',
        badgeClass: 'consulta-de-participantes__background-7',
        badgeTextoClass: 'consulta-de-participantes__text-21',
        badgeIcon: `
            <svg viewBox="0 0 13.333 13.333" xmlns="http://www.w3.org/2000/svg" fill="none" class="consulta-de-participantes__icon-12" role="img">
              <path d="M5.733 9.733 L10.433 5.033 L9.5 4.1 L5.733 7.867 L3.833 5.967 L2.9 6.9 L5.733 9.733 Z" fill="rgb(6, 95, 70)" />
            </svg>
        `
    },
    pendente_pagamento: {
        texto: 'Pendente de Pagamento',
        artigoClass: 'consulta-de-participantes__article-item-4-pendente',
        badgeClass: 'consulta-de-participantes__background-11',
        badgeTextoClass: 'consulta-de-participantes__text-41',
        badgeIcon: `
            <svg viewBox="0 0 13.333 13.333" xmlns="http://www.w3.org/2000/svg" fill="none" class="consulta-de-participantes__icon-17" role="img">
              <path d="M6.667 0 C2.987 0 0 2.987 0 6.667 C0 10.347 2.987 13.333 6.667 13.333 C10.347 13.333 13.333 10.347 13.333 6.667 C13.333 2.987 10.347 0 6.667 0 Z M7 3.333 L6 3.333 L6 7.333 L9.5 9.433 L10 8.6 L7 6.833 Z" fill="rgb(133, 83, 0)" />
            </svg>
        `
    },
    lista_espera: {
        texto: 'Lista de Espera',
        artigoClass: 'consulta-de-participantes__article-item-5-lista-de-espera',
        badgeClass: 'consulta-de-participantes__background-13',
        badgeTextoClass: 'consulta-de-participantes__text-51',
        badgeIcon: `
            <svg viewBox="0 0 10.667 13.333" xmlns="http://www.w3.org/2000/svg" fill="none" class="consulta-de-participantes__icon-20" role="img">
              <path d="M2.667 12 L8 12 L8 10 C8 9.267 7.733 8.64 7.213 8.12 C6.693 7.6 6.067 7.333 5.333 7.333 C4.6 7.333 3.973 7.6 3.453 8.12 C2.933 8.64 2.667 9.267 2.667 10 Z" fill="rgb(0, 109, 65)" />
            </svg>
        `
    },
    cancelada: {
        texto: 'Cancelada',
        artigoClass: 'consulta-de-participantes__article-item-6-cancelada',
        badgeClass: 'consulta-de-participantes__background-15',
        badgeTextoClass: 'consulta-de-participantes__text-61',
        badgeIcon: `
            <svg viewBox="0 0 13.333 13.333" xmlns="http://www.w3.org/2000/svg" fill="none" class="consulta-de-participantes__icon-22" role="img">
              <path d="M4.267 10 L6.667 7.6 L9.067 10 L10 9.067 L7.6 6.667 L10 4.267 L9.067 3.333 L6.667 5.733 L4.267 3.333 L3.333 4.267 L5.733 6.667 L3.333 9.067 Z" fill="rgb(186, 26, 26)" />
            </svg>
        `
    }
};

document.addEventListener('DOMContentLoaded', () => {
    if (!isAuthenticated()) {
        window.location.href = resolveAppUrl('usuarios/login/login.html');
        return;
    }

    atualizarCabecalhoUsuario('participantes');

    const selectEvento = document.getElementById('filtro-evento');
    if (selectEvento) {
        selectEvento.addEventListener('change', (e) => {
            eventoSelecionadoId = e.target.value || null;
            carregarParticipantes();
        });
    }

    const btnAplicar = document.getElementById('btn-aplicar-filtros');
    if (btnAplicar) btnAplicar.addEventListener('click', () => carregarParticipantes());

    const btnLimpar = document.getElementById('btn-limpar-filtros');
    if (btnLimpar) {
        btnLimpar.addEventListener('click', () => {
            const inputBusca = document.getElementById('filtro-busca');
            const selectStatus = document.getElementById('filtro-status');
            if (inputBusca) inputBusca.value = '';
            if (selectStatus) selectStatus.value = '';
            carregarParticipantes();
        });
    }

    const inputBusca = document.getElementById('filtro-busca');
    if (inputBusca) {
        inputBusca.addEventListener('keyup', (e) => {
            if (e.key === 'Enter') carregarParticipantes();
        });
    }

    const selectStatus = document.getElementById('filtro-status');
    if (selectStatus) {
        selectStatus.addEventListener('change', () => carregarParticipantes());
    }

    const btnExportarCsv = document.getElementById('btn-exportar-csv');
    if (btnExportarCsv) {
        btnExportarCsv.addEventListener('click', () => exportarParaCsv());
    }

    carregarMeusEventos();
});

async function carregarMeusEventos() {
    const select = document.getElementById('filtro-evento');
    if (!select) return;

    const urlParams = new URLSearchParams(window.location.search);
    const eventoDaUrl = urlParams.get('evento');

    try {
        const response = await apiFetch('/eventos/meus-eventos/');
        if (!response.ok) {
            showAlert('mensagem-alerta', 'Não foi possível carregar a lista dos seus eventos.', 'danger');
            return;
        }

        const eventos = await response.json();
        if (eventos.length === 0) {
            select.innerHTML = '<option value="">Nenhum evento encontrado</option>';
            const semEv = document.getElementById('sem-participantes');
            if (semEv) {
                semEv.style.display = 'block';
                semEv.innerHTML = `
                    <h3 style="font-size: 18px; font-weight: 700; color: #0f172a; margin: 0 0 8px 0;">Nenhum Evento Encontrado</h3>
                    <p style="font-size: 14px; color: #64748b; margin: 0;">Você ainda não possui eventos cadastrados para visualizar participantes.</p>
                `;
            }
            return;
        }

        select.innerHTML = '<option value="">Selecione um evento...</option>';

        eventos.forEach(ev => {
            const option = document.createElement('option');
            option.value = ev.id;
            option.textContent = `${ev.nome} (${formatarData(ev.data)})`;
            select.appendChild(option);
        });

        if (eventoDaUrl && eventos.some(ev => String(ev.id) === String(eventoDaUrl))) {
            select.value = eventoDaUrl;
            eventoSelecionadoId = eventoDaUrl;
            carregarParticipantes();
        } else if (eventos.length === 1) {
            select.value = eventos[0].id;
            eventoSelecionadoId = eventos[0].id;
            carregarParticipantes();
        } else {
            const semEv = document.getElementById('sem-participantes');
            if (semEv) {
                semEv.style.display = 'block';
                semEv.innerHTML = `
                    <h3 style="font-size: 18px; font-weight: 700; color: #0f172a; margin: 0 0 8px 0;">Selecione um Evento</h3>
                    <p style="font-size: 14px; color: #64748b; margin: 0;">Selecione um dos seus eventos no filtro acima para visualizar a lista de inscritos.</p>
                `;
            }
        }
    } catch (error) {
        showAlert('mensagem-alerta', 'Erro de conexão com o servidor do SGIE.', 'danger');
    }
}

async function carregarParticipantes() {
    clearAlert('mensagem-alerta');
    const spinner = document.getElementById('loading-spinner');
    const lista = document.getElementById('lista-participantes');
    const vazio = document.getElementById('sem-participantes');
    const contador = document.getElementById('contador-participantes');

    if (!eventoSelecionadoId) {
        if (vazio) {
            vazio.style.display = 'block';
            const selectEvento = document.getElementById('filtro-evento');
            const semEventosCadastrados = selectEvento && selectEvento.options.length <= 1 && selectEvento.value === '' && selectEvento.options[0]?.text.includes('Nenhum evento');
            if (semEventosCadastrados) {
                vazio.innerHTML = `
                    <h3 style="font-size: 18px; font-weight: 700; color: #0f172a; margin: 0 0 8px 0;">Nenhum Evento Encontrado</h3>
                    <p style="font-size: 14px; color: #64748b; margin: 0;">Você ainda não possui eventos cadastrados para visualizar participantes.</p>
                `;
            } else {
                vazio.innerHTML = `
                    <h3 style="font-size: 18px; font-weight: 700; color: #0f172a; margin: 0 0 8px 0;">Selecione um Evento</h3>
                    <p style="font-size: 14px; color: #64748b; margin: 0;">Selecione um dos seus eventos no filtro acima para visualizar a lista de inscritos.</p>
                `;
            }
        }
        if (lista) lista.style.display = 'none';
        if (contador) contador.textContent = '0 participantes encontrados';
        return;
    }

    if (vazio) vazio.style.display = 'none';
    if (spinner) spinner.style.display = 'block';
    if (lista) lista.style.display = 'none';

    const params = new URLSearchParams();
    const busca = document.getElementById('filtro-busca') ? document.getElementById('filtro-busca').value.trim() : '';
    const statusFiltro = document.getElementById('filtro-status') ? document.getElementById('filtro-status').value : '';

    if (busca) params.append('busca', busca);
    if (statusFiltro) params.append('status', statusFiltro);

    const queryString = params.toString();
    const url = `/eventos/${eventoSelecionadoId}/inscritos/${queryString ? `?${queryString}` : ''}`;

    try {
        const response = await apiFetch(url);
        if (spinner) spinner.style.display = 'none';

        if (response.status === 403) {
            showAlert('mensagem-alerta', 'Você não tem permissão para consultar os participantes deste evento.', 'danger');
            return;
        }
        if (response.status === 404) {
            showAlert('mensagem-alerta', 'Evento não encontrado.', 'danger');
            return;
        }

        if (response.ok) {
            todosParticipantes = await response.json();

            // Atualiza contadores globais do evento
            atualizarContadoresParticipantes(todosParticipantes);

            if (contador) {
                contador.textContent = `${todosParticipantes.length} participante(s) encontrado(s)`;
            }

            if (!todosParticipantes || todosParticipantes.length === 0) {
                if (vazio) {
                    vazio.style.display = 'block';
                    vazio.innerHTML = `
                        <h3 style="font-size: 18px; font-weight: 700; color: #0f172a; margin: 0 0 8px 0;">Nenhum participante encontrado</h3>
                        <p style="font-size: 14px; color: #64748b; margin: 0;">${busca || statusFiltro ? 'Tente ajustar os filtros informados.' : 'Quando alguém se inscrever neste evento, a inscrição aparecerá aqui.'}</p>
                    `;
                }
                if (lista) lista.style.display = 'none';
                return;
            }

            renderizarParticipantes(todosParticipantes);
            if (lista) lista.style.display = 'flex';
        } else {
            const err = await response.json().catch(() => ({}));
            showAlert('mensagem-alerta', err.detail || 'Não foi possível carregar os participantes.', 'danger');
        }
    } catch (error) {
        if (spinner) spinner.style.display = 'none';
        showAlert('mensagem-alerta', 'Erro de conexão com o servidor do SGIE.', 'danger');
    }
}

function atualizarContadoresParticipantes(participantes) {
    const counts = {
        confirmada: 0,
        pendente_pagamento: 0,
        lista_espera: 0,
        cancelada: 0
    };

    participantes.forEach(p => {
        if (counts[p.status] !== undefined) {
            counts[p.status]++;
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

function renderizarParticipantes(participantes) {
    const lista = document.getElementById('lista-participantes');
    if (!lista) return;

    lista.innerHTML = '';

    participantes.forEach(p => {
        const cfg = STATUS_CONFIG_PARTICIPANTE[p.status] || {
            texto: p.status_display || p.status,
            artigoClass: 'consulta-de-participantes__article-item-1-confirmada',
            badgeClass: 'consulta-de-participantes__background-7',
            badgeTextoClass: 'consulta-de-participantes__text-21',
            badgeIcon: ''
        };

        const card = document.createElement('div');
        card.className = cfg.artigoClass;
        card.style.display = 'flex';
        card.style.justifyContent = 'space-between';
        card.style.alignItems = 'center';
        card.style.flexWrap = 'wrap';
        card.style.gap = '16px';
        card.style.padding = '18px 24px';
        card.style.borderRadius = '14px';
        card.style.background = '#ffffff';
        card.style.border = '1px solid #e2e8f0';
        card.style.marginBottom = '12px';

        const nome = p.participante_nome || p.participante_email || 'Participante';
        const partes = nome.trim().split(/\s+/);
        const iniciais = partes.length > 1
            ? (partes[0][0] + partes[partes.length - 1][0]).toUpperCase()
            : (partes[0] ? partes[0].slice(0, 2).toUpperCase() : 'SG');

        const email = p.participante_email || 'E-mail não informado';
        const dataFmt = formatarDataHora(p.data_inscricao);
        const comprovanteUrl = p.comprovante ? obterUrlComprovanteSegura(p.comprovante) : null;

        card.innerHTML = `
            <div style="display: flex; align-items: center; gap: 16px; flex: 1 1 360px;">
                <div style="width: 44px; height: 44px; border-radius: 50%; background: #ecfdf5; color: #006d41; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 16px; flex-shrink: 0;">
                    ${iniciais}
                </div>
                <div style="min-width: 0;">
                    <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                        <p style="font-size: 16px; font-weight: 700; color: #0f172a; margin: 0;">${nome}</p>
                        <span style="font-size: 13px; color: #94a3b8;">•</span>
                        <span style="font-size: 13px; color: #64748b; font-family: monospace;">#${p.id}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-top: 4px;">
                        <span style="font-size: 13px; color: #64748b;">${email}</span>
                        <span style="font-size: 13px; color: #94a3b8;">•</span>
                        <span style="font-size: 13px; color: #64748b;">Inscrito em: ${dataFmt}</span>
                    </div>
                </div>
            </div>

            <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                <div class="${cfg.badgeClass}">
                    <div class="consulta-de-participantes__container-45">
                        ${cfg.badgeIcon}
                    </div>
                    <p class="${cfg.badgeTextoClass}">${p.status_display || cfg.texto}</p>
                </div>

                <button type="button" class="btn btn-sm btn-outline" onclick="alternarDetalhesParticipante(${p.id})" style="padding: 8px 14px; font-size: 13px; font-weight: 600; border-radius: 8px; background: #f8fafc; border: 1.5px solid #cbd5e1; cursor: pointer;">
                    <span id="rotulo-detalhes-p-${p.id}">Ver Detalhes</span>
                </button>
            </div>

            <div id="detalhes-participante-${p.id}" style="display: none; width: 100%; margin-top: 8px; padding: 14px 16px; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;">
                <p style="margin: 0 0 6px 0; font-size: 13px; color: #475569;"><strong>Campos adicionais / observações:</strong> ${formatarDadosAdicionais(p.dados_adicionais)}</p>
                ${comprovanteUrl ? `<p style="margin: 0; font-size: 13px;"><a href="${comprovanteUrl}" target="_blank" rel="noopener noreferrer" style="color: #006d41; font-weight: 700; text-decoration: underline;">Visualizar comprovante de vínculo enviado</a></p>` : '<p style="margin: 0; font-size: 13px; color: #64748b;">Nenhum comprovante anexado.</p>'}
            </div>
        `;

        lista.appendChild(card);
    });
}

function alternarDetalhesParticipante(id) {
    const el = document.getElementById(`detalhes-participante-${id}`);
    const rotulo = document.getElementById(`rotulo-detalhes-p-${id}`);
    if (!el) return;
    const visivel = el.style.display !== 'none';
    el.style.display = visivel ? 'none' : 'block';
    if (rotulo) rotulo.textContent = visivel ? 'Ver Detalhes' : 'Ocultar Detalhes';
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

function obterUrlComprovanteSegura(comprovante) {
    if (!comprovante) return null;
    try {
        const baseUrl = typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : window.location.origin;
        const url = new URL(String(comprovante), `${baseUrl}/`);
        return url.href;
    } catch {
        return null;
    }
}

function exportarParaCsv() {
    if (!todosParticipantes || todosParticipantes.length === 0) {
        showAlert('mensagem-alerta', 'Não há participantes para exportar neste momento.', 'warning');
        return;
    }

    const cabecalhos = ['ID', 'Nome', 'E-mail', 'Status', 'Data Inscrição', 'Dados Adicionais'];
    const linhas = todosParticipantes.map(p => {
        const id = p.id;
        const nome = `"${(p.participante_nome || '').replace(/"/g, '""')}"`;
        const email = `"${(p.participante_email || '').replace(/"/g, '""')}"`;
        const status = `"${(p.status_display || p.status || '').replace(/"/g, '""')}"`;
        const data = `"${(formatarDataHora(p.data_inscricao) || '').replace(/"/g, '""')}"`;
        const adicionais = `"${(formatarDadosAdicionais(p.dados_adicionais) || '').replace(/"/g, '""')}"`;
        return [id, nome, email, status, data, adicionais].join(';');
    });

    const conteudoCsv = [cabecalhos.join(';'), ...linhas].join('\r\n');
    const blob = new Blob(['\ufeff' + conteudoCsv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `participantes_evento_${eventoSelecionadoId || 'sgie'}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}
