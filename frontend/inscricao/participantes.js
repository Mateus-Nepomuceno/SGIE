const STATUS_LABELS_PARTICIPANTE = {
    confirmada: { texto: 'Confirmada', classe: 'badge-open' },
    pendente_pagamento: { texto: 'Pendente de Pagamento', classe: 'badge-config' },
    lista_espera: { texto: 'Em Lista de Espera', classe: 'badge-secondary' },
    cancelada: { texto: 'Cancelada', classe: 'badge-canceled' },
};

let participantesAtuais = [];
let eventoSelecionadoId = null;

document.addEventListener('DOMContentLoaded', () => {
    if (!isAuthenticated()) {
        window.location.href = resolveAppUrl('usuarios/login.html');
        return;
    }

    atualizarCabecalhoUsuario('participantes');

    document.getElementById('filtro-evento').addEventListener('change', (e) => {
        eventoSelecionadoId = e.target.value || null;
        atualizarLinkEvento();
        carregarParticipantes();
    });
    document.getElementById('btn-aplicar-filtros').addEventListener('click', () => carregarParticipantes());
    document.getElementById('btn-limpar-filtros').addEventListener('click', () => {
        document.getElementById('filtro-busca').value = '';
        document.getElementById('filtro-status').value = '';
        carregarParticipantes();
    });
    document.getElementById('filtro-busca').addEventListener('keyup', (e) => {
        if (e.key === 'Enter') carregarParticipantes();
    });

    carregarMeusEventos();
});

async function carregarMeusEventos() {
    const select = document.getElementById('filtro-evento');
    const params = new URLSearchParams(window.location.search);
    const eventoDaUrl = params.get('evento');

    try {
        const response = await apiFetch('/eventos/meus-eventos/');
        if (!response.ok) {
            showAlert('mensagem-alerta', 'Não foi possível carregar a lista dos seus eventos.', 'danger');
            return;
        }

        const eventos = await response.json();

        eventos.forEach(ev => {
            const option = document.createElement('option');
            option.value = ev.id;
            option.textContent = ev.nome;
            select.appendChild(option);
        });

        if (eventoDaUrl && eventos.some(ev => String(ev.id) === String(eventoDaUrl))) {
            select.value = eventoDaUrl;
            eventoSelecionadoId = eventoDaUrl;
            atualizarLinkEvento();
            carregarParticipantes();
        } else if (eventos.length === 0) {
            const semEvento = document.getElementById('sem-evento-selecionado');
            semEvento.querySelector('h3').textContent = 'Você ainda não organiza nenhum evento';
            semEvento.querySelector('p').textContent = 'Assim que você criar ou passar a organizar um evento, poderá consultar os participantes aqui.';
        }
    } catch (error) {
        showAlert('mensagem-alerta', 'Erro de conexão com o servidor do SGIE.', 'danger');
    }
}

function atualizarLinkEvento() {
    const link = document.getElementById('link-voltar-evento');
    if (eventoSelecionadoId) {
        link.href = `../eventos/detalhes_evento.html?id=${eventoSelecionadoId}`;
        link.style.display = 'inline-flex';
    } else {
        link.style.display = 'none';
    }
}

async function carregarParticipantes() {
    clearAlert('mensagem-alerta');
    const semEvento = document.getElementById('sem-evento-selecionado');
    const spinner = document.getElementById('loading-spinner');
    const lista = document.getElementById('lista-participantes');
    const vazio = document.getElementById('sem-participantes');
    const contador = document.getElementById('contador-resultados');

    if (!eventoSelecionadoId) {
        semEvento.style.display = 'block';
        spinner.style.display = 'none';
        lista.style.display = 'none';
        vazio.style.display = 'none';
        contador.style.display = 'none';
        return;
    }

    semEvento.style.display = 'none';
    spinner.style.display = 'block';
    lista.style.display = 'none';
    vazio.style.display = 'none';
    contador.style.display = 'none';

    const params = new URLSearchParams();
    const busca = document.getElementById('filtro-busca').value.trim();
    const statusFiltro = document.getElementById('filtro-status').value;

    if (busca) params.append('busca', busca);
    if (statusFiltro) params.append('status', statusFiltro);

    const queryString = params.toString();
    const url = `/eventos/${eventoSelecionadoId}/inscritos/${queryString ? `?${queryString}` : ''}`;

    try {
        const response = await apiFetch(url);
        spinner.style.display = 'none';

        if (response.status === 403) {
            showAlert('mensagem-alerta', 'Você não tem permissão para consultar os participantes deste evento.', 'danger');
            return;
        }
        if (response.status === 404) {
            showAlert('mensagem-alerta', 'Evento não encontrado.', 'danger');
            return;
        }

        if (response.ok) {
            participantesAtuais = await response.json();

            contador.textContent = `${participantesAtuais.length} participante(s) encontrado(s)`;
            contador.style.display = 'block';

            if (!participantesAtuais || participantesAtuais.length === 0) {
                vazio.style.display = 'block';
                if (busca || statusFiltro) {
                    document.getElementById('titulo-vazio').textContent = 'Nenhum participante encontrado';
                    document.getElementById('desc-vazio').textContent = 'Tente ajustar os filtros aplicados.';
                } else {
                    document.getElementById('titulo-vazio').textContent = 'Ainda não há inscrições';
                    document.getElementById('desc-vazio').textContent = 'Quando alguém se inscrever neste evento, a inscrição aparecerá aqui.';
                }
                return;
            }

            renderizarParticipantes(participantesAtuais);
            lista.style.display = 'flex';
        } else {
            const err = await response.json().catch(() => ({}));
            showAlert('mensagem-alerta', err.detail || 'Não foi possível carregar os participantes.', 'danger');
        }
    } catch (error) {
        spinner.style.display = 'none';
        showAlert('mensagem-alerta', 'Erro de conexão com o servidor do SGIE.', 'danger');
    }
}

function renderizarParticipantes(participantes) {
    const lista = document.getElementById('lista-participantes');
    lista.replaceChildren();

    participantes.forEach(p => {
        const info = STATUS_LABELS_PARTICIPANTE[p.status] || {
            texto: p.status_display || p.status || '—',
            classe: 'badge-secondary',
        };

        const card = document.createElement('article');
        card.className = 'inscricao-card';

        const header = document.createElement('div');
        header.className = 'card-header-bar';

        const badge = document.createElement('span');
        badge.className = `badge ${info.classe}`;
        badge.textContent = p.status_display || info.texto;
        header.appendChild(badge);

        const body = document.createElement('div');
        body.className = 'card-body';

        const title = document.createElement('h2');
        title.className = 'card-title';
        title.textContent = p.participante_nome || 'Participante não identificado';
        body.appendChild(title);

        const metaList = document.createElement('ul');
        metaList.className = 'card-meta-list';

        const emailItem = document.createElement('li');
        emailItem.className = 'card-meta-item';
        const emailLabel = document.createElement('strong');
        emailLabel.textContent = 'E-mail:';
        emailItem.append(emailLabel, document.createTextNode(` ${p.participante_email || '—'}`));

        const dataItem = document.createElement('li');
        dataItem.className = 'card-meta-item';
        const dataLabel = document.createElement('strong');
        dataLabel.textContent = 'Inscrito em:';
        dataItem.append(dataLabel, document.createTextNode(` ${formatarDataHora(p.data_inscricao)}`));

        metaList.append(emailItem, dataItem);
        body.appendChild(metaList);

        const detalhes = document.createElement('div');
        detalhes.id = `detalhes-${p.id}`;
        detalhes.className = 'inscricao-detalhes';
        detalhes.style.display = 'none';

        const dataList = document.createElement('dl');
        dataList.className = 'data-list';

        const adicionaisDiv = document.createElement('div');
        const adicionaisDt = document.createElement('dt');
        adicionaisDt.textContent = 'Campos adicionais informados:';
        const adicionaisDd = document.createElement('dd');
        adicionaisDd.textContent = formatarDadosAdicionaisParticipante(p.dados_adicionais);
        adicionaisDiv.append(adicionaisDt, adicionaisDd);
        dataList.appendChild(adicionaisDiv);

        if (p.comprovante) {
            const comprovanteDiv = document.createElement('div');
            const comprovanteDt = document.createElement('dt');
            comprovanteDt.textContent = 'Comprovante enviado:';

            const comprovanteDd = document.createElement('dd');
            const comprovanteLink = document.createElement('a');
            const comprovanteUrl = obterUrlComprovanteSegura(p.comprovante);

            if (comprovanteUrl) {
                comprovanteLink.href = comprovanteUrl;
                comprovanteLink.target = '_blank';
                comprovanteLink.rel = 'noopener noreferrer';
                comprovanteLink.textContent = 'Visualizar comprovante';
                comprovanteDd.appendChild(comprovanteLink);
            } else {
                comprovanteDd.textContent = 'Comprovante indisponível.';
            }

            comprovanteDiv.append(comprovanteDt, comprovanteDd);
            dataList.appendChild(comprovanteDiv);
        }

        detalhes.appendChild(dataList);
        body.appendChild(detalhes);

        const footer = document.createElement('div');
        footer.className = 'card-footer';

        const buttonGroup = document.createElement('div');
        buttonGroup.className = 'btn-group';

        const detalhesButton = document.createElement('button');
        detalhesButton.type = 'button';
        detalhesButton.className = 'btn btn-sm btn-outline';
        detalhesButton.textContent = 'Ver Detalhes';
        detalhesButton.addEventListener('click', () => alternarDetalhesParticipante(p.id));

        buttonGroup.appendChild(detalhesButton);
        footer.appendChild(buttonGroup);

        card.append(header, body, footer);
        lista.appendChild(card);
    });
}

function formatarDadosAdicionaisParticipante(dados) {
    if (!dados) return '—';
    if (typeof dados === 'string') return dados.trim() ? dados : '—';
    if (typeof dados === 'object') {
        const entradas = Object.entries(dados).filter(([, valor]) => valor !== null && valor !== undefined && valor !== '');
        if (entradas.length === 0) return '—';
        return entradas.map(([campo, valor]) => `${campo}: ${valor}`).join(' · ');
    }
    return String(dados);
}

function obterUrlComprovanteSegura(comprovante) {
    if (!comprovante) return null;

    try {
        const baseUrl = typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : window.location.origin;
        const url = new URL(String(comprovante), `${baseUrl}/`);

        if (!['http:', 'https:'].includes(url.protocol)) {
            return null;
        }

        return url.href;
    } catch {
        return null;
    }
}

function alternarDetalhesParticipante(id) {
    const el = document.getElementById(`detalhes-${id}`);
    if (!el) return;
    el.style.display = el.style.display === 'none' ? 'block' : 'none';
}
