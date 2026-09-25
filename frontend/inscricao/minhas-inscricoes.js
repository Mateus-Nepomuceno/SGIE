const STATUS_LABELS = {
    confirmada: { texto: 'Confirmada', classe: 'badge-open' },
    pendente_pagamento: { texto: 'Pendente de Pagamento', classe: 'badge-config' },
    lista_espera: { texto: 'Em Lista de Espera', classe: 'badge-secondary' },
    cancelada: { texto: 'Cancelada', classe: 'badge-canceled' },
};

let minhasInscricoes = [];

document.addEventListener('DOMContentLoaded', () => {
    if (!isAuthenticated()) {
        window.location.href = resolveAppUrl('usuarios/login.html');
        return;
    }

    atualizarCabecalhoUsuario('minhas-inscricoes');

    document.getElementById('btn-aplicar-filtros').addEventListener('click', () => carregarInscricoes());
    document.getElementById('btn-limpar-filtros').addEventListener('click', () => {
        document.getElementById('filtro-busca').value = '';
        document.getElementById('filtro-status').value = '';
        carregarInscricoes();
    });
    document.getElementById('filtro-busca').addEventListener('keyup', (e) => {
        if (e.key === 'Enter') carregarInscricoes();
    });
    document.getElementById('btn-fechar-ingresso').addEventListener('click', fecharIngresso);
    document.getElementById('overlay-ingresso').addEventListener('click', (e) => {
        if (e.target.id === 'overlay-ingresso') fecharIngresso();
    });

    carregarInscricoes();
});

async function carregarInscricoes() {
    clearAlert('mensagem-alerta');
    const spinner = document.getElementById('loading-spinner');
    const lista = document.getElementById('lista-inscricoes');
    const vazio = document.getElementById('sem-inscricoes');

    spinner.style.display = 'block';
    lista.style.display = 'none';
    vazio.style.display = 'none';

    const params = new URLSearchParams();
    const busca = document.getElementById('filtro-busca').value.trim();
    const statusFiltro = document.getElementById('filtro-status').value;

    if (busca) params.append('busca', busca);
    if (statusFiltro) params.append('status', statusFiltro);

    const queryString = params.toString();
    const url = queryString ? `/inscricoes/minhas/?${queryString}` : '/inscricoes/minhas/';

    try {
        const response = await apiFetch(url);
        spinner.style.display = 'none';

        if (response.ok) {
            minhasInscricoes = await response.json();

            if (!minhasInscricoes || minhasInscricoes.length === 0) {
                vazio.style.display = 'block';
                if (busca || statusFiltro) {
                    document.getElementById('titulo-vazio').textContent = 'Nenhuma inscrição encontrada';
                    document.getElementById('desc-vazio').textContent = 'Tente ajustar os filtros aplicados.';
                } else {
                    document.getElementById('titulo-vazio').textContent = 'Você ainda não possui inscrições';
                    document.getElementById('desc-vazio').innerHTML = 'Explore os eventos disponíveis na <a href="../index.html">página inicial</a> e realize sua primeira inscrição.';
                }
                return;
            }

            renderizarInscricoes(minhasInscricoes);
            lista.style.display = 'flex';
        } else {
            const err = await response.json();
            showAlert('mensagem-alerta', err.detail || 'Não foi possível carregar suas inscrições.', 'danger');
        }
    } catch (error) {
        spinner.style.display = 'none';
        showAlert('mensagem-alerta', 'Erro de conexão com o servidor do SGIE.', 'danger');
    }
}

function renderizarInscricoes(inscricoes) {
    const lista = document.getElementById('lista-inscricoes');
    lista.innerHTML = '';

    inscricoes.forEach(insc => {
        const info = STATUS_LABELS[insc.status] || { texto: insc.status_display, classe: 'badge-secondary' };

        const card = document.createElement('article');
        card.className = 'inscricao-card';

        let situacaoExtra = '';
        if (insc.status === 'lista_espera' && insc.posicao_lista_espera) {
            situacaoExtra = `<p class="card-meta-item"><strong>Posição na fila:</strong> ${insc.posicao_lista_espera}º lugar</p>`;
        }
        if (insc.status === 'pendente_pagamento') {
            situacaoExtra = insc.evento_necessita_comprovante && insc.comprovante
                ? `<p class="card-meta-item">Comprovante enviado — aguardando confirmação do pagamento.</p>`
                : `<p class="card-meta-item">Finalize o pagamento para confirmar sua vaga.</p>`;
        }

        let acoesHtml = '';
        if (insc.status === 'confirmada') {
            acoesHtml += `<button type="button" class="btn btn-sm btn-primary" onclick="abrirIngresso(${insc.id})">Ver Ingresso</button>`;
        }
        if (insc.pode_cancelar) {
            const labelCancelar = insc.status === 'lista_espera' ? 'Desistir da Lista de Espera' : 'Cancelar Inscrição';
            acoesHtml += `<button type="button" class="btn btn-sm btn-danger" onclick="cancelarInscricao(${insc.id})">${labelCancelar}</button>`;
        }
        acoesHtml += `<button type="button" class="btn btn-sm btn-outline" onclick="alternarDetalhes(${insc.id})">Ver Detalhes</button>`;

        card.innerHTML = `
            <div class="card-header-bar">
                <span class="badge ${info.classe}">${insc.status_display || info.texto}</span>
                <span class="pill">${insc.evento_categoria || ''}</span>
            </div>
            <div class="card-body">
                <h2 class="card-title">${insc.evento_nome}</h2>
                <ul class="card-meta-list">
                    <li class="card-meta-item"><strong>Data:</strong> ${formatarData(insc.evento_data)} às ${formatarHora(insc.evento_hora_inicio)} (${insc.evento_modalidade})</li>
                    <li class="card-meta-item"><strong>Local:</strong> ${insc.evento_local}</li>
                    <li class="card-meta-item"><strong>Inscrito em:</strong> ${formatarDataHora(insc.data_inscricao)}</li>
                </ul>
                ${situacaoExtra}
                <div id="detalhes-${insc.id}" class="inscricao-detalhes" style="display: none;">
                    <dl class="data-list">
                        <div>
                            <dt>Valor da inscrição:</dt>
                            <dd>${insc.evento_e_gratuito ? 'Gratuito' : formatarMoeda(insc.evento_preco)}</dd>
                        </div>
                        <div>
                            <dt>Campos adicionais informados:</dt>
                            <dd>${formatarDadosAdicionais(insc.dados_adicionais)}</dd>
                        </div>
                        ${insc.comprovante ? `<div><dt>Comprovante enviado:</dt><dd><a href="${insc.comprovante}" target="_blank" rel="noopener">Visualizar comprovante</a></dd></div>` : ''}
                    </dl>
                </div>
            </div>
            <div class="card-footer">
                <div class="btn-group">
                    ${acoesHtml}
                </div>
            </div>
        `;

        lista.appendChild(card);
    });
}

function formatarDadosAdicionais(dados) {
    if (!dados) return '—';
    if (typeof dados === 'string') return dados.trim() ? dados : '—';
    if (typeof dados === 'object') {
        const entradas = Object.entries(dados).filter(([, v]) => v !== null && v !== undefined && v !== '');
        if (entradas.length === 0) return '—';
        return entradas.map(([campo, valor]) => `${campo}: ${valor}`).join(' · ');
    }
    return String(dados);
}

function alternarDetalhes(id) {
    const el = document.getElementById(`detalhes-${id}`);
    if (!el) return;
    el.style.display = el.style.display === 'none' ? 'block' : 'none';
}

async function cancelarInscricao(id) {
    const inscricao = minhasInscricoes.find(i => i.id === id);
    const mensagem = inscricao && inscricao.status === 'lista_espera'
        ? 'Deseja realmente desistir da lista de espera deste evento?'
        : 'Deseja realmente cancelar esta inscrição? Essa ação não pode ser desfeita.';

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
        showAlert('mensagem-alerta', 'Erro de conexão com o servidor do SGIE.', 'danger');
    }
}

function abrirIngresso(id) {
    const insc = minhasInscricoes.find(i => i.id === id);
    if (!insc || !insc.codigo_ingresso) return;

    const user = getUser();
    const nomeParticipante = user ? (user.nome_completo || user.email) : '';
    const qrData = encodeURIComponent(insc.codigo_ingresso);
    const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${qrData}`;

    const conteudo = document.getElementById('conteudo-ingresso');
    conteudo.innerHTML = `
        <div class="ticket" id="ticket-imprimivel">
            <h2 class="ticket-titulo">${insc.evento_nome}</h2>
            <p class="ticket-subtitulo">${formatarData(insc.evento_data)} às ${formatarHora(insc.evento_hora_inicio)} — ${insc.evento_local}</p>
            <img src="${qrUrl}" alt="QR Code do ingresso" class="ticket-qr">
            <p class="ticket-codigo">${insc.codigo_ingresso}</p>
            <p class="ticket-participante">${nomeParticipante}</p>
            <p class="ticket-aviso">Apresente este QR Code no credenciamento do evento.</p>
        </div>
        <div class="btn-group" style="justify-content: center; margin-top: 1rem;">
            <button type="button" class="btn btn-sm btn-secondary" onclick="window.print()">Imprimir Ingresso</button>
        </div>
    `;

    document.getElementById('overlay-ingresso').style.display = 'flex';
}

function fecharIngresso() {
    document.getElementById('overlay-ingresso').style.display = 'none';
}
