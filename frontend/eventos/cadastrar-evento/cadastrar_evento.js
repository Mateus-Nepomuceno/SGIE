/* SGIE — cadastrar_evento.js
 * Fluxo de cadastro de eventos integrado à API e visual padronizado.
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Verificação de Autenticação
    if (!isAuthenticated()) {
        window.location.href = resolveAppUrl('usuarios/login/login.html');
        return;
    }

    // 2. Atualiza o cabeçalho global padrão do SGIE
    atualizarCabecalhoUsuario('novo');

    // 3. Verificação de perfil de Organizador
    const usuario = getUser();
    const bannerAviso = document.getElementById('banner-aviso-organizador');
    const ehOrganizador = usuario && (usuario.eh_organizador || usuario.is_organizador || usuario.acesso_admin || usuario.superusuario);
    if (bannerAviso && ehOrganizador) {
        bannerAviso.style.display = 'none';
    }

    // 4. Elementos do Formulário
    const form = document.getElementById('form-cadastrar-evento');
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
    const campoGratuito = document.getElementById('campo-gratuito');
    const campoPreco = document.getElementById('campo-preco');
    const blocoPreco = document.getElementById('bloco-preco');
    const campoComprovante = document.getElementById('campo-comprovante');
    const campoAceitaSubmissao = document.getElementById('campo-aceita-submissao');
    const blocoDatasSubmissao = document.getElementById('bloco-datas-submissao');
    const campoSubmissaoInicio = document.getElementById('campo-submissao-inicio');
    const campoSubmissaoFim = document.getElementById('campo-submissao-fim');
    const campoProgramacao = document.getElementById('campo-programacao');
    const contadorDescricao = document.getElementById('contador-descricao');
    const feedbackCap = document.getElementById('texto-capitalizacao');

    // 5. Elementos de Prévia (Live Preview Card)
    const prevStatus = document.getElementById('preview-status');
    const prevPreco = document.getElementById('preview-preco');
    const prevCategoria = document.getElementById('preview-categoria');
    const prevNome = document.getElementById('preview-nome');
    const prevDescricao = document.getElementById('preview-descricao');
    const prevData = document.getElementById('preview-data');
    const prevHorario = document.getElementById('preview-horario');
    const prevModalidade = document.getElementById('preview-modalidade');
    const prevCapacidade = document.getElementById('preview-capacidade');

    // Inicializar data padrão (hoje + 30 dias para respeitar antecedência mínima sugerida)
    const dataSugerida = new Date();
    dataSugerida.setDate(dataSugerida.getDate() + 65);
    campoData.value = dataSugerida.toISOString().split('T')[0];

    // Atualiza a prévia em tempo real
    function atualizarPrevia() {
        // Nome
        const nome = (campoNome.value || '').trim();
        prevNome.textContent = nome || 'Título do Evento Acadêmico';

        // Validação visual de capitalização de título
        if (nome) {
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

        // Descrição e Contador
        const desc = (campoDescricao.value || '').trim();
        if (contadorDescricao) {
            contadorDescricao.textContent = `${campoDescricao.value.length} / 2000 caracteres`;
        }
        prevDescricao.textContent = desc || 'Descrição preliminar do evento, objetivos formativos e temática central...';

        // Categoria
        const cat = campoCategoria.value || 'Simpósio';
        prevCategoria.textContent = cat.toUpperCase();

        // Modalidade
        const mod = campoModalidade.value || 'Presencial';
        prevModalidade.textContent = mod;

        // Mostrar / ocultar link de transmissão conforme modalidade
        const containerVirtual = document.getElementById('container-transmissao-virtual');
        if (containerVirtual) {
            containerVirtual.style.display = (mod === 'Híbrido' || mod === 'On-line') ? 'flex' : 'none';
        }

        // Gratuito / Preço
        if (campoGratuito.checked) {
            if (blocoPreco) blocoPreco.style.display = 'none';
            prevPreco.textContent = 'Gratuito';
        } else {
            if (blocoPreco) blocoPreco.style.display = 'inline-flex';
            const val = parseFloat(campoPreco.value) || 0;
            prevPreco.textContent = val > 0 ? formatarMoeda(val) : 'A Definir';
        }

        // Data
        if (campoData.value) {
            const [ano, mes, dia] = campoData.value.split('-');
            const d = new Date(Number(ano), Number(mes) - 1, Number(dia));
            prevData.textContent = d.toLocaleDateString('pt-BR', { day: 'numeric', month: 'short', year: 'numeric' });
        } else {
            prevData.textContent = 'Data a definir';
        }

        // Horário
        const hInicio = campoHoraInicio.value || '08:30';
        const hFim = campoHoraFim.value || '17:30';
        prevHorario.textContent = `${hInicio} às ${hFim}`;

        // Capacidade
        const cap = parseInt(campoCapacidade.value, 10) || 0;
        prevCapacidade.textContent = `${cap} vagas disponíveis`;
    }

    // Ouvintes de evento para campos do formulário
    campoNome.addEventListener('input', atualizarPrevia);
    campoDescricao.addEventListener('input', atualizarPrevia);
    campoCategoria.addEventListener('change', atualizarPrevia);
    campoModalidade.addEventListener('change', atualizarPrevia);
    campoData.addEventListener('change', atualizarPrevia);
    campoHoraInicio.addEventListener('change', atualizarPrevia);
    campoHoraFim.addEventListener('change', atualizarPrevia);
    campoCapacidade.addEventListener('input', atualizarPrevia);
    campoGratuito.addEventListener('change', atualizarPrevia);
    campoPreco.addEventListener('input', atualizarPrevia);

    if (campoAceitaSubmissao && blocoDatasSubmissao) {
        campoAceitaSubmissao.addEventListener('change', () => {
            blocoDatasSubmissao.style.display = campoAceitaSubmissao.checked ? 'grid' : 'none';
        });
    }

    // Inicializar visual de prévia na carga inicial
    atualizarPrevia();

    // 6. Envio do Formulário para a API
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        clearAlert('mensagem-alerta');

        const btnSubmit = document.getElementById('btn-submit-evento');
        const txtBotaoOriginal = btnSubmit ? btnSubmit.innerHTML : '';
        if (btnSubmit) {
            btnSubmit.disabled = true;
            btnSubmit.style.opacity = '0.7';
        }

        try {
            const nome = campoNome.value.trim();
            const descricao = campoDescricao.value.trim();
            const categoria = campoCategoria.value;
            const modalidade = campoModalidade.value;
            const visibilidade = campoVisibilidade.value;
            const data = campoData.value;
            const horaInicio = campoHoraInicio.value;
            const horaFim = campoHoraFim.value;
            const localTipo = campoLocalTipo.value;
            const local = campoLocal.value.trim();
            const capacidade = parseInt(campoCapacidade.value, 10);
            const eGratuito = campoGratuito.checked;
            const preco = eGratuito ? '0.00' : (parseFloat(campoPreco.value) || 0).toFixed(2);
            const necessitaComprovante = campoComprovante ? campoComprovante.checked : false;
            const programacaoGeral = campoProgramacao ? campoProgramacao.value.trim() : '';

            // Validações básicas de frontend
            if (!nome || !descricao || !data || !horaInicio || !horaFim || !local || !capacidade) {
                showAlert('mensagem-alerta', 'Por favor, preencha todos os campos obrigatórios destacados com asterisco (*).', 'danger');
                if (btnSubmit) { btnSubmit.disabled = false; btnSubmit.style.opacity = '1'; }
                return;
            }

            if (horaFim <= horaInicio) {
                showAlert('mensagem-alerta', 'O horário de término deve ser estritamente posterior ao horário de início.', 'danger');
                if (btnSubmit) { btnSubmit.disabled = false; btnSubmit.style.opacity = '1'; }
                return;
            }

            const payload = {
                nome,
                descricao,
                categoria,
                modalidade,
                visibilidade,
                data,
                hora_inicio: horaInicio,
                hora_fim: horaFim,
                local_tipo: localTipo,
                local,
                capacidade,
                e_gratuito: eGratuito,
                preco,
                necessita_comprovante: necessitaComprovante,
                programacao_geral: programacaoGeral,
            };

            // Regra de submissão opcional
            if (campoAceitaSubmissao && campoAceitaSubmissao.checked) {
                const subInicio = campoSubmissaoInicio ? campoSubmissaoInicio.value : '';
                const subFim = campoSubmissaoFim ? campoSubmissaoFim.value : '';
                if (!subInicio || !subFim) {
                    showAlert('mensagem-alerta', 'Para habilitar submissões de trabalhos, defina o início e o término do prazo.', 'danger');
                    if (btnSubmit) { btnSubmit.disabled = false; btnSubmit.style.opacity = '1'; }
                    return;
                }
                payload.regra_submissao = {
                    aceita_submissao: true,
                    data_hora_inicio: subInicio,
                    data_hora_fim: subFim,
                };
            }

            const response = await apiFetch('/eventos/', {
                method: 'POST',
                body: JSON.stringify(payload),
            });

            const dataResposta = await response.json().catch(() => ({}));

            if (!response.ok) {
                let msg = 'Erro ao cadastrar evento.';
                if (dataResposta.detail) {
                    msg = dataResposta.detail;
                } else if (typeof dataResposta === 'object') {
                    const erros = Object.entries(dataResposta)
                        .map(([campo, errs]) => `${campo}: ${Array.isArray(errs) ? errs.join(', ') : errs}`)
                        .join(' | ');
                    if (erros) msg = erros;
                }
                showAlert('mensagem-alerta', msg, 'danger');
                window.scrollTo({ top: 0, behavior: 'smooth' });
                if (btnSubmit) { btnSubmit.disabled = false; btnSubmit.style.opacity = '1'; }
                return;
            }

            showAlert('mensagem-alerta', 'Evento cadastrado com sucesso! Redirecionando para a página do evento...', 'success');
            window.scrollTo({ top: 0, behavior: 'smooth' });

            const novoId = dataResposta.id || (dataResposta.evento && dataResposta.evento.id);
            setTimeout(() => {
                if (novoId) {
                    window.location.href = `../detalhes-do-evento/index.html?id=${novoId}`;
                } else {
                    window.location.href = '../../index.html?tab=meus-eventos';
                }
            }, 1200);

        } catch (err) {
            console.error('Erro de requisição:', err);
            showAlert('mensagem-alerta', 'Não foi possível conectar com o servidor do SGIE.', 'danger');
            window.scrollTo({ top: 0, behavior: 'smooth' });
            if (btnSubmit) { btnSubmit.disabled = false; btnSubmit.style.opacity = '1'; }
        }
    });
});
