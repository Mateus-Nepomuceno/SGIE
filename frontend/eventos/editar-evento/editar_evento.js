/* SGIE — editar_evento.js
 * Fluxo de edição com verificação de prazos regimentais e integridade acadêmica.
 */

document.addEventListener('DOMContentLoaded', async () => {
    // 1. Verificação de Autenticação
    if (!isAuthenticated()) {
        window.location.href = resolveAppUrl('usuarios/login/login.html');
        return;
    }

    // 2. Cabeçalho padrão do SGIE
    atualizarCabecalhoUsuario('eventos');

    // 3. Obter ID do Evento
    const params = new URLSearchParams(window.location.search);
    const eventoId = params.get('id');

    if (!eventoId) {
        mostrarErro('Nenhum evento especificado para edição.');
        return;
    }

    // 4. Carregar dados do evento
    await carregarDadosEvento(eventoId);
});

function mostrarErro(msg) {
    const alerta = document.getElementById('mensagem-alerta');
    if (alerta) {
        alerta.className = 'alert alert-danger';
        alerta.innerHTML = `<strong>Atenção:</strong> ${msg} <br><br><a href="../../index.html" class="btn btn-secondary btn-sm" style="margin-top: 8px;">← Voltar para Eventos</a>`;
        alerta.style.display = 'block';
    }
    const form = document.getElementById('form-editar-evento');
    if (form) form.style.display = 'none';
}

async function carregarDadosEvento(id) {
    clearAlert('mensagem-alerta');
    try {
        const resp = await apiFetch(`/eventos/${id}/`);
        if (!resp.ok) {
            mostrarErro('Evento não encontrado ou indisponível.');
            return;
        }

        const ev = await resp.json();
        const user = getUser();

        // Verificação de Permissão
        const ehRepresentante = Boolean(user && user.id && ev.usuario_representante && String(user.id) === String(ev.usuario_representante));
        const ehStaff = Boolean(user && (user.acesso_admin || user.superusuario));
        const ehEquipe = Boolean(user && user.id && ev.organizadores && ev.organizadores.some(o => String(o.usuario) === String(user.id)));

        if (!ehRepresentante && !ehStaff && !ehEquipe) {
            mostrarErro('Você não possui autorização para editar este evento acadêmico.');
            return;
        }

        configurarFormulario(ev);

    } catch (err) {
        console.error('Erro ao buscar evento para edição:', err);
        mostrarErro('Erro de comunicação com o servidor do SGIE.');
    }
}

function configurarFormulario(ev) {
    // Título e código no cabeçalho
    const elCodigo = document.getElementById('editar-subtitulo-codigo');
    if (elCodigo) {
        elCodigo.textContent = `${ev.nome} • Código #${ev.id} • Situação: ${ev.status_display || ev.status}`;
    }

    // Campos do formulário
    const form = document.getElementById('form-editar-evento');
    const campoNome = document.getElementById('campo-nome');
    const campoDescricao = document.getElementById('campo-descricao');
    const campoCategoria = document.getElementById('campo-categoria');
    const campoModalidade = document.getElementById('campo-modalidade');
    const campoVisibilidade = document.getElementById('campo-visibilidade');
    const campoData = document.getElementById('campo-data');
    const campoHoraInicio = document.getElementById('campo-hora-inicio');
    const campoHoraFim = document.getElementById('campo-hora-fim');
    const campoLocalTipo = document.getElementById('campo-local-tipo');
    const campoLocal = document.getElementById('campo-local');
    const campoLinkTransmissao = document.getElementById('campo-link-transmissao');
    const campoCapacidade = document.getElementById('campo-capacidade');
    const campoProgramacao = document.getElementById('campo-programacao');
    const contadorDescricao = document.getElementById('contador-descricao');
    const feedbackCap = document.getElementById('texto-capitalizacao');

    // Pré-preenchimento
    campoNome.value = ev.nome || '';
    campoDescricao.value = ev.descricao || '';
    if (ev.categoria) campoCategoria.value = ev.categoria;
    if (ev.modalidade) campoModalidade.value = ev.modalidade;
    if (ev.visibilidade) campoVisibilidade.value = ev.visibilidade;
    if (ev.data) campoData.value = ev.data.split('T')[0];
    if (ev.hora_inicio) campoHoraInicio.value = ev.hora_inicio.slice(0, 5);
    if (ev.hora_fim) campoHoraFim.value = ev.hora_fim.slice(0, 5);
    if (ev.local_tipo) campoLocalTipo.value = ev.local_tipo;
    campoLocal.value = ev.local || '';
    campoCapacidade.value = ev.capacidade || 250;
    campoProgramacao.value = ev.programacao_geral || '';

    // Elementos de Prévia
    const prevStatus = document.getElementById('preview-status');
    const prevPreco = document.getElementById('preview-preco');
    const prevCategoria = document.getElementById('preview-categoria');
    const prevNome = document.getElementById('preview-nome');
    const prevDescricao = document.getElementById('preview-descricao');
    const prevData = document.getElementById('preview-data');
    const prevHorario = document.getElementById('preview-horario');
    const prevModalidade = document.getElementById('preview-modalidade');
    const prevCapacidade = document.getElementById('preview-capacidade');

    if (prevStatus) prevStatus.textContent = ev.status_display || ev.status || 'Publicado';
    if (prevPreco) prevPreco.textContent = ev.e_gratuito ? 'Gratuito' : (formatarMoeda ? formatarMoeda(ev.preco) : `R$ ${ev.preco}`);

    // Verificação de Evento Cancelado
    const alertaCancelado = document.getElementById('alerta-evento-cancelado');
    const ehCancelado = ev.status === 'Cancelado';
    if (alertaCancelado) {
        alertaCancelado.style.display = ehCancelado ? 'flex' : 'none';
    }

    // Verificação de Prazos Regimentais (Congelamento de Campos)
    const alertaData = document.getElementById('alerta-bloqueio-data');
    const tagDataCongelada = document.getElementById('tag-data-congelada');
    if (ev.pode_alterar_data === false) {
        campoData.disabled = true;
        if (alertaData) alertaData.style.display = 'flex';
        if (tagDataCongelada) tagDataCongelada.style.display = 'block';
    } else {
        campoData.disabled = false;
        if (alertaData) alertaData.style.display = 'none';
        if (tagDataCongelada) tagDataCongelada.style.display = 'none';
    }

    const alertaHorario = document.getElementById('alerta-bloqueio-horario');
    const alertaDescricao = document.getElementById('alerta-bloqueio-descricao');
    if (ev.pode_alterar_detalhes === false) {
        campoHoraInicio.disabled = true;
        campoHoraFim.disabled = true;
        campoDescricao.disabled = true;
        if (alertaHorario) alertaHorario.style.display = 'flex';
        if (alertaDescricao) alertaDescricao.style.display = 'flex';
    } else {
        campoHoraInicio.disabled = false;
        campoHoraFim.disabled = false;
        campoDescricao.disabled = false;
        if (alertaHorario) alertaHorario.style.display = 'none';
        if (alertaDescricao) alertaDescricao.style.display = 'none';
    }

    // Se o evento estiver cancelado, desabilita todo o formulário de edição
    if (ehCancelado && form) {
        form.querySelectorAll('input, select, textarea, button[type="submit"]').forEach(el => {
            el.disabled = true;
        });
    }

    // Gerenciador de visibilidade do container de alertas: só exibe espaço se houver algum alerta ativo
    const containerAlertas = document.querySelector('.editar-evento__alertas-dinamicos-de-bloqueio-de-prazos-rfs13');
    if (containerAlertas) {
        const algumVisivel = [alertaCancelado, alertaData, alertaHorario, alertaDescricao].some(
            el => el && el.style.display === 'flex'
        );
        containerAlertas.style.display = algumVisivel ? 'flex' : 'none';
    }

    function atualizarPrevia() {
        const nome = (campoNome.value || '').trim();
        if (prevNome) prevNome.textContent = nome || 'Título do Evento';

        if (nome && feedbackCap) {
            const palavras = nome.split(/\s+/);
            const maiusculas = palavras.filter(p => p && p[0] === p[0].toUpperCase());
            if (maiusculas.length >= Math.ceil(palavras.length * 0.5)) {
                feedbackCap.textContent = 'Capitalização adequada identificada e válida para o catálogo.';
                feedbackCap.style.color = 'rgb(0, 108, 74)';
            } else {
                feedbackCap.textContent = 'Recomendado: utilize Estilo Título com as primeiras letras maiúsculas.';
                feedbackCap.style.color = 'rgb(133, 83, 0)';
            }
        }

        const desc = (campoDescricao.value || '').trim();
        if (contadorDescricao) contadorDescricao.textContent = `${campoDescricao.value.length} / 2000 caracteres`;
        if (prevDescricao) prevDescricao.textContent = desc || 'Descrição do evento...';

        if (prevCategoria) prevCategoria.textContent = (campoCategoria.value || 'Simpósio').toUpperCase();
        if (prevModalidade) prevModalidade.textContent = campoModalidade.value || 'Presencial';

        const containerVirtual = document.getElementById('container-transmissao-virtual');
        if (containerVirtual) {
            containerVirtual.style.display = (campoModalidade.value === 'Híbrido' || campoModalidade.value === 'On-line') ? 'flex' : 'none';
        }

        if (campoData.value && prevData) {
            const [ano, mes, dia] = campoData.value.split('-');
            const d = new Date(Number(ano), Number(mes) - 1, Number(dia));
            prevData.textContent = d.toLocaleDateString('pt-BR', { day: 'numeric', month: 'short', year: 'numeric' });
        }

        if (prevHorario) {
            prevHorario.textContent = `${campoHoraInicio.value || '08:30'} às ${campoHoraFim.value || '17:30'}`;
        }

        if (prevCapacidade) {
            const cap = parseInt(campoCapacidade.value, 10) || 0;
            prevCapacidade.textContent = `${cap} vagas disponíveis`;
        }
    }

    // Ouvintes
    campoNome.addEventListener('input', atualizarPrevia);
    campoDescricao.addEventListener('input', atualizarPrevia);
    campoCategoria.addEventListener('change', atualizarPrevia);
    campoModalidade.addEventListener('change', atualizarPrevia);
    campoData.addEventListener('change', atualizarPrevia);
    campoHoraInicio.addEventListener('change', atualizarPrevia);
    campoHoraFim.addEventListener('change', atualizarPrevia);
    campoCapacidade.addEventListener('input', atualizarPrevia);

    atualizarPrevia();

    // 5. Envio de Atualização (PATCH)
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        clearAlert('mensagem-alerta');

        const btnSubmit = document.getElementById('btn-submit-edicao');
        if (btnSubmit) {
            btnSubmit.disabled = true;
            btnSubmit.style.opacity = '0.7';
        }

        try {
            const formatarTitulo = (str) => str ? str.trim().split(/\s+/).map(p => p ? p.charAt(0).toUpperCase() + p.slice(1) : '').join(' ') : '';
            const rawNome = campoNome.value.trim();
            const nome = formatarTitulo(rawNome);
            if (nome) campoNome.value = nome;
            const descricao = campoDescricao.value.trim();
            const categoria = campoCategoria.value;
            const modalidade = campoModalidade.value;
            const visibilidade = campoVisibilidade.value;
            const localTipo = campoLocalTipo.value;
            const local = campoLocal.value.trim();
            const capacidade = parseInt(campoCapacidade.value, 10);
            const programacaoGeral = campoProgramacao ? campoProgramacao.value.trim() : '';

            if (!nome || !descricao || !local || !capacidade) {
                showAlert('mensagem-alerta', 'Preencha todos os campos obrigatórios (*).', 'danger');
                if (btnSubmit) { btnSubmit.disabled = false; btnSubmit.style.opacity = '1'; }
                return;
            }

            const payload = {
                nome,
                descricao,
                categoria,
                modalidade,
                visibilidade,
                local_tipo: localTipo,
                local,
                capacidade,
                programacao_geral: programacaoGeral,
            };

            // Adicionar data e horários caso não estejam congelados
            if (ev.pode_alterar_data !== false && campoData.value) {
                payload.data = campoData.value;
            }
            if (ev.pode_alterar_detalhes !== false) {
                if (campoHoraFim.value <= campoHoraInicio.value) {
                    showAlert('mensagem-alerta', 'O horário de término deve ser posterior ao horário de início.', 'danger');
                    if (btnSubmit) { btnSubmit.disabled = false; btnSubmit.style.opacity = '1'; }
                    return;
                }
                payload.hora_inicio = campoHoraInicio.value;
                payload.hora_fim = campoHoraFim.value;
            }

            const respUpdate = await apiFetch(`/eventos/${ev.id}/`, {
                method: 'PATCH',
                body: JSON.stringify(payload),
            });

            const dataResp = await respUpdate.json().catch(() => ({}));

            if (!respUpdate.ok) {
                let msg = 'Erro ao atualizar dados do evento.';
                if (dataResp.detail) msg = dataResp.detail;
                else if (typeof dataResp === 'object') {
                    msg = Object.entries(dataResp)
                        .map(([c, errs]) => `${c}: ${Array.isArray(errs) ? errs.join(', ') : errs}`)
                        .join(' | ');
                }
                showAlert('mensagem-alerta', msg, 'danger');
                window.scrollTo({ top: 0, behavior: 'smooth' });
                if (btnSubmit) { btnSubmit.disabled = false; btnSubmit.style.opacity = '1'; }
                return;
            }

            showAlert('mensagem-alerta', 'Alterações salvas com sucesso! Redirecionando...', 'success');
            window.scrollTo({ top: 0, behavior: 'smooth' });

            setTimeout(() => {
                window.location.href = `../detalhes-do-evento/index.html?id=${ev.id}`;
            }, 1000);

        } catch (err) {
            console.error('Erro na atualização:', err);
            showAlert('mensagem-alerta', 'Falha ao conectar com o servidor do SGIE.', 'danger');
            window.scrollTo({ top: 0, behavior: 'smooth' });
            if (btnSubmit) { btnSubmit.disabled = false; btnSubmit.style.opacity = '1'; }
        }
    });
}
