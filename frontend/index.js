/* SGIE — index.js (tela Explorar Eventos) */

let abaAtual = 'todos';

const $ = (id) => document.getElementById(id);

const TEMAS_CATEGORIA = {
    'Congresso': ['amber', 'atom'], 'Feira': ['amber', 'atom'], 'Workshop': ['amber', 'atom'],
    'Oficina': ['amber', 'atom'], 'Competição': ['amber', 'star'], 'Festival': ['amber', 'star'],
    'Lançamento de Produto': ['amber', 'star'],
    'Curso': ['green', 'book'], 'Mini-curso': ['green', 'book'], 'Treinamento': ['green', 'book'],
    'Roda de Conversa': ['green', 'book'],
};

const DECORACOES = {
    globe: '<circle cx="50" cy="50" r="46"/><ellipse cx="50" cy="50" rx="20" ry="46"/><ellipse cx="50" cy="50" rx="46" ry="20"/><path d="M50 4v92M4 50h92"/>',
    atom: '<ellipse cx="50" cy="50" rx="46" ry="17"/><ellipse cx="50" cy="50" rx="46" ry="17" transform="rotate(60 50 50)"/><ellipse cx="50" cy="50" rx="46" ry="17" transform="rotate(120 50 50)"/><circle cx="50" cy="50" r="6" fill="currentColor"/>',
    book: '<path d="M50 24C38 14 20 14 6 20v64c14-6 32-6 44 4 12-10 30-10 44-4V20c-14-6-32-6-44 4zM50 24v64"/>',
    star: '<path d="m50 6 13 28 30 4-22 21 6 30-27-15-27 15 6-30L7 38l30-4z"/>',
};

const ESTADOS_STATUS = {
    'Inscrições abertas': '', 'Publicado': '', 'Em realização': 'st-warn',
    'Finalizado': 'st-neutral', 'Arquivado': 'st-neutral', 'Rascunho': 'st-warn',
    'Configuração': 'st-warn', 'Cancelado': 'st-danger',
};

function esc(valor) {
    return String(valor ?? '').replace(/[&<>"']/g, (c) => (
        { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    ));
}

function dataCurta(dataIso) {
    const [a, m, d] = String(dataIso || '').split('T')[0].split('-').map(Number);
    if (!a) return '—';
    return new Date(a, m - 1, d).toLocaleDateString('pt-BR', { day: 'numeric', month: 'short', year: 'numeric' });
}

function usuarioEhStaff(user) {
    return Boolean(user && (user.acesso_admin || user.superusuario));
}

/* ---------- Inicialização ---------- */

document.addEventListener('DOMContentLoaded', () => {
    atualizarCabecalhoUsuario('eventos');

    if (getUser() && isAuthenticated()) {
        $('tabs-nav').hidden = false;
        atualizarContadorMeusEventos();

        const urlParams = new URLSearchParams(window.location.search);
        const tabParam = urlParams.get('tab');
        if (tabParam === 'meus' || tabParam === 'meus-eventos') {
            alternarAba('meus-eventos');
            return;
        }
    }

    $('tab-todos').addEventListener('click', () => alternarAba('todos'));
    $('tab-meus-eventos').addEventListener('click', () => alternarAba('meus-eventos'));
    $('btn-aplicar-filtros').addEventListener('click', carregarEventos);
    $('btn-limpar-filtros').addEventListener('click', () => {
        ['filtro-busca', 'filtro-categoria', 'filtro-modalidade', 'filtro-preco'].forEach((id) => { $(id).value = ''; });
        carregarEventos();
    });
    $('filtro-busca').addEventListener('keyup', (e) => { if (e.key === 'Enter') carregarEventos(); });
    ['filtro-categoria', 'filtro-modalidade', 'filtro-preco'].forEach((id) => $(id).addEventListener('change', carregarEventos));

    carregarEventos();
});

function alternarAba(aba) {
    abaAtual = aba;
    $('tab-todos').classList.toggle('active', aba === 'todos');
    $('tab-meus-eventos').classList.toggle('active', aba === 'meus-eventos');
    $('toolbar-filtros').hidden = aba !== 'todos';
    carregarEventos();
}

async function atualizarContadorMeusEventos() {
    try {
        const resp = await apiFetch('/eventos/meus-eventos/');
        if (resp.ok) $('badge-total-meus').textContent = (await resp.json()).length;
    } catch { /* contador é opcional */ }
}

/* ---------- Carregamento ---------- */

async function carregarEventos() {
    clearAlert('mensagem-alerta');
    $('loading-spinner').hidden = false;
    $('grid-eventos').hidden = true;
    $('sem-eventos').hidden = true;

    let url = '/eventos/meus-eventos/';
    if (abaAtual === 'todos') {
        const params = new URLSearchParams();
        const filtros = { search: $('filtro-busca').value.trim(), categoria: $('filtro-categoria').value,
            modalidade: $('filtro-modalidade').value, e_gratuito: $('filtro-preco').value };
        Object.entries(filtros).forEach(([k, v]) => { if (v) params.append(k, v); });
        url = `/eventos/${params.toString() ? `?${params}` : ''}`;
    }

    try {
        const resp = await apiFetch(url);
        $('loading-spinner').hidden = true;

        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            showAlert('mensagem-alerta', err.detail || 'Não foi possível carregar os eventos.', 'danger');
            return;
        }

        const dados = await resp.json();
        const eventos = Array.isArray(dados) ? dados : (dados.results || []);
        if (abaAtual === 'meus-eventos') $('badge-total-meus').textContent = eventos.length;

        if (!eventos.length) return mostrarVazio();
        renderizarEventos(eventos);
        $('grid-eventos').hidden = false;
    } catch {
        $('loading-spinner').hidden = true;
        showAlert('mensagem-alerta', 'Erro de conexão com o servidor do SGIE.', 'danger');
    }
}

function mostrarVazio() {
    const meus = abaAtual === 'meus-eventos';
    $('titulo-vazio').textContent = meus ? 'Você ainda não cadastrou eventos' : 'Nenhum evento encontrado';
    $('desc-vazio').innerHTML = meus
        ? 'Crie seu primeiro evento em <a href="eventos/cadastrar-evento/index.html">Cadastrar Evento</a>.'
        : 'Tente ajustar os filtros aplicados.';
    $('sem-eventos').hidden = false;
}

/* ---------- Renderização ---------- */

function renderizarEventos(eventos) {
    const user = getUser();
    const logado = Boolean(user && isAuthenticated());
    $('grid-eventos').innerHTML = eventos.map((ev) => htmlCard(ev, user, logado)).join('');
}

function htmlCard(ev, user, logado) {
    const temVagas = Number.isFinite(ev.vagas_disponiveis);
    const esgotado = temVagas && ev.vagas_disponiveis <= 0 && ev.status !== 'Finalizado' && ev.status !== 'Cancelado';
    const dono = Boolean(
        logado && user && user.id && ev.usuario_representante && String(ev.usuario_representante).toLowerCase() === String(user.id).toLowerCase()
    );
    const gerencia = dono;

    let [tom, deco] = TEMAS_CATEGORIA[ev.categoria] || ['green', 'globe'];
    if (esgotado) tom = 'gray';

    const estado = esgotado ? 'st-full' : (ESTADOS_STATUS[ev.status] ?? 'st-neutral');
    const rotuloStatus = esgotado ? 'Vagas Esgotadas' : (ev.status_display || ev.status);
    const preco = ev.e_gratuito
        ? '<span class="pill pill-price">Gratuito</span>'
        : `<span class="pill pill-price paid">${esc(formatarMoeda(ev.preco))}</span>`;

    const categoria = ev.categoria === 'Outro' && ev.categoria_personalizada ? ev.categoria_personalizada : (ev.categoria_display || ev.categoria);
    const rodapeCapa = logado
        ? `<div class="ev-row"><span class="pill pill-cat">${esc(categoria)}</span>${dono
            ? '<span class="pill pill-owner"><span class="icon icon-shield-check"></span>Você é Organizador(a)</span>' : ''}</div>`
        : '<div></div>';

    const iconeModalidade = ev.modalidade === 'Híbrido' ? 'icon-repeat' : 'icon-monitor';
    const linhaVagas = !temVagas
        ? `<li><span class="icon icon-users"></span>Capacidade: ${esc(ev.capacidade)} participantes</li>`
        : esgotado
            ? '<li class="full"><span class="icon icon-alert-circle"></span>0 vagas disponíveis (Lista de espera)</li>'
            : `<li class="strong"><span class="icon icon-users"></span><span><b>${ev.vagas_disponiveis}</b> vagas disponíveis (de ${esc(ev.capacidade)})</span></li>`;

    const detalhes = `eventos/detalhes-do-evento/index.html?id=${encodeURIComponent(ev.id)}`;
    let acoes;
    if (gerencia) {
        acoes = `<a href="eventos/editar-evento/index.html?id=${encodeURIComponent(ev.id)}" class="btn btn-secondary"><span class="icon icon-pencil"></span>Editar</a>
                 <a href="${detalhes}" class="btn btn-primary"><span class="icon icon-settings"></span>Gerenciar</a>`;
    } else if (logado && !esgotado && ev.status === 'Inscrições abertas' && ev.inscricoes_abertas !== false) {
        acoes = `<a href="${detalhes}" class="btn btn-secondary btn-detalhes">Detalhes</a>
                 <a href="inscricao/realizar-inscricao/index.html?evento=${encodeURIComponent(ev.id)}" class="btn btn-primary"><span class="icon icon-user-plus"></span>Realizar Inscrição</a>`;
    } else {
        acoes = `<a href="${detalhes}" class="btn btn-soft">Ver Detalhes${logado ? '<span class="icon icon-arrow-right"></span>' : ''}</a>`;
    }

    return `
    <article class="ev-card tone-${tom}">
        <div class="ev-cover">
            <svg class="ev-deco" viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true">${DECORACOES[deco]}</svg>
            <div class="ev-row">
                <span class="pill pill-status ${estado}">${esgotado ? '' : '<span class="dot"></span>'}${esc(rotuloStatus)}</span>
                ${preco}
            </div>
            ${rodapeCapa}
        </div>
        <div class="ev-body">
            <h2 class="ev-title"><a href="${detalhes}">${esc(ev.nome)}</a></h2>
            <p class="ev-desc">${esc(ev.descricao || 'Sem descrição cadastrada.')}</p>
            <ul class="ev-meta">
                <li><span class="icon icon-calendar"></span>${esc(dataCurta(ev.data))}</li>
                <li><span class="icon icon-clock"></span>${esc(formatarHora(ev.hora_inicio))} às ${esc(formatarHora(ev.hora_fim))}</li>
                <li><span class="icon ${iconeModalidade}"></span>${esc(ev.modalidade_display || ev.modalidade)}</li>
                <li><span class="icon icon-map-pin"></span>${esc(ev.local)}</li>
                ${linhaVagas}
            </ul>
            <div class="ev-actions">${acoes}</div>
        </div>
    </article>`;
}
