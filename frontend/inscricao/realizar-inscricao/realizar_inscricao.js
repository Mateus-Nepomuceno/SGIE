document.addEventListener('DOMContentLoaded', async () => {
    if (!isAuthenticated()) {
        window.location.href = resolveAppUrl('usuarios/login/login.html');
        return;
    }

    atualizarCabecalhoUsuario('');

    const urlParams = new URLSearchParams(window.location.search);
    const eventoId = urlParams.get('evento');

    if (!eventoId) {
        showAlert('mensagem-alerta', 'Evento não especificado. Redirecionando para a lista de eventos...', 'danger');
        setTimeout(() => {
            window.location.href = resolveAppUrl('index.html');
        }, 2000);
        return;
    }

    const inputEventoId = document.getElementById('evento_id');
    if (inputEventoId) inputEventoId.value = eventoId;

    // Preenche dados do usuário autenticado
    const user = getUser();
    if (user) {
        const nome = user.nome_completo || user.email || 'Participante';
        const partesNome = nome.trim().split(/\s+/);
        const iniciais = partesNome.length > 1
            ? (partesNome[0][0] + partesNome[partesNome.length - 1][0]).toUpperCase()
            : (partesNome[0] ? partesNome[0].slice(0, 2).toUpperCase() : 'SG');

        const elIniciais = document.getElementById('usuario-iniciais');
        if (elIniciais) elIniciais.textContent = iniciais;

        const elNome = document.getElementById('usuario-nome');
        if (elNome) elNome.textContent = nome;

        const elEmailInfo = document.getElementById('usuario-email-info');
        if (elEmailInfo) {
            const instituicao = user.instituicao ? ` • ${user.instituicao}` : '';
            const matricula = user.matricula ? ` • Matrícula: ${user.matricula}` : '';
            elEmailInfo.textContent = `${user.email}${matricula}${instituicao}`;
        }

        const elCpf = document.getElementById('usuario-cpf');
        if (elCpf) {
            elCpf.textContent = user.cpf ? mascaraCPF(user.cpf) : 'Não informado';
        }

        const elTipo = document.getElementById('usuario-tipo');
        if (elTipo) {
            elTipo.textContent = user.perfil_display || user.perfil || 'Participante / Ouvinte';
        }
    }

    // Carrega dados do evento
    let evento = null;
    try {
        const response = await apiFetch(`/eventos/${eventoId}/`);
        if (!response.ok) {
            showAlert('mensagem-alerta', 'Evento não encontrado ou indisponível.', 'danger');
            return;
        }
        evento = await response.json();

        // Consulta lista de espera
        let listaEsperaCount = 0;
        try {
            const respEspera = await apiFetch(`/eventos/${eventoId}/inscritos/?status=lista_espera`);
            if (respEspera.ok) {
                const listaEspera = await respEspera.json();
                listaEsperaCount = Array.isArray(listaEspera) ? listaEspera.length : 0;
            }
        } catch {
            // Silencioso se não tiver permissão para ver lista
        }

        // Atualiza cabeçalho da página
        const elEventoTitulo = document.getElementById('evento-titulo');
        if (elEventoTitulo) elEventoTitulo.textContent = `Inscrição: ${evento.nome}`;

        const elEventoSubtitulo = document.getElementById('evento-subtitulo');
        if (elEventoSubtitulo) {
            const dataFmt = formatarData(evento.data);
            const horaFmt = formatarHora(evento.hora_inicio);
            elEventoSubtitulo.textContent = `${evento.nome} • ${dataFmt} às ${horaFmt} • ${evento.local}`;
        }

        // Atualiza comprovante (obrigatório / opcional / oculto)
        const secaoComprovante = document.getElementById('secao-comprovante');
        const comprovanteObrigatorio = document.getElementById('comprovante-obrigatorio');
        const inputComprovante = document.getElementById('campo-comprovante');
        if (evento.necessita_comprovante) {
            if (secaoComprovante) secaoComprovante.style.display = 'block';
            if (comprovanteObrigatorio) comprovanteObrigatorio.style.display = 'inline';
            if (inputComprovante) inputComprovante.required = true;
        } else {
            if (comprovanteObrigatorio) comprovanteObrigatorio.style.display = 'none';
            if (inputComprovante) inputComprovante.required = false;
        }

        // Atualiza card de prévia lateral
        const prevStatus = document.getElementById('preview-status');
        if (prevStatus) {
            if (evento.vagas_disponiveis === 0) {
                prevStatus.textContent = 'Fila de Espera';
            } else {
                prevStatus.textContent = evento.status_display || evento.status || 'Inscrições abertas';
            }
        }

        const prevPreco = document.getElementById('preview-preco');
        if (prevPreco) {
            prevPreco.textContent = evento.e_gratuito ? 'Gratuito' : formatarMoeda(evento.preco);
        }

        const prevCat = document.getElementById('preview-categoria');
        if (prevCat) {
            prevCat.textContent = (evento.categoria || 'EVENTO').toUpperCase();
        }

        const prevNome = document.getElementById('preview-nome');
        if (prevNome) {
            prevNome.textContent = evento.nome;
        }

        const prevDesc = document.getElementById('preview-descricao');
        if (prevDesc) {
            prevDesc.textContent = evento.descricao || '';
        }

        const prevData = document.getElementById('preview-data');
        if (prevData) {
            prevData.textContent = formatarData(evento.data);
        }

        const prevHorario = document.getElementById('preview-horario');
        if (prevHorario) {
            prevHorario.textContent = `${formatarHora(evento.hora_inicio)} às ${formatarHora(evento.hora_fim)}`;
        }

        const prevMod = document.getElementById('preview-modalidade');
        if (prevMod) {
            prevMod.textContent = evento.modalidade_display || evento.modalidade || 'Presencial';
        }

        const prevVagas = document.getElementById('preview-vagas');
        if (prevVagas) {
            if (evento.vagas_disponiveis === 0) {
                prevVagas.textContent = `Vagas esgotadas (${listaEsperaCount} na fila)`;
            } else {
                prevVagas.textContent = `${evento.vagas_disponiveis} vaga(s) restante(s)`;
            }
        }

        const prevLink = document.getElementById('preview-link-detalhes');
        if (prevLink) {
            prevLink.href = resolveAppUrl(`eventos/detalhes-do-evento/index.html?id=${evento.id}`);
        }

        const btnSubmitTexto = document.getElementById('texto-btn-submit');
        if (btnSubmitTexto) {
            if (evento.vagas_disponiveis === 0) {
                btnSubmitTexto.textContent = 'Entrar na Lista de Espera';
            } else {
                btnSubmitTexto.textContent = 'Confirmar e Realizar Inscrição';
            }
        }

    } catch (err) {
        showAlert('mensagem-alerta', 'Erro ao carregar dados do evento.', 'danger');
        return;
    }

    // Manipulação de Upload do Comprovante (click e drag-and-drop)
    const fileInput = document.getElementById('campo-comprovante');
    const dropzone = document.getElementById('dropzone-comprovante');
    const btnSelecionarArquivo = document.getElementById('btn-selecionar-arquivo');
    const nomeArquivo = document.getElementById('nome-arquivo-selecionado');

    if (btnSelecionarArquivo && fileInput) {
        btnSelecionarArquivo.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            fileInput.click();
        });
    }

    if (dropzone && fileInput) {
        dropzone.addEventListener('click', () => {
            fileInput.click();
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove('dragover');
            });
        });

        dropzone.addEventListener('drop', (e) => {
            if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files;
                atualizarNomeArquivo(fileInput.files[0]);
            }
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files && fileInput.files.length > 0) {
                atualizarNomeArquivo(fileInput.files[0]);
            }
        });
    }

    function atualizarNomeArquivo(file) {
        if (!file) return;
        const maxMB = 10;
        if (file.size > maxMB * 1024 * 1024) {
            showAlert('mensagem-alerta', `O arquivo excede o limite máximo de ${maxMB} MB.`, 'warning');
            fileInput.value = '';
            if (nomeArquivo) nomeArquivo.textContent = 'Clique para selecionar ou arraste o arquivo aqui';
            return;
        }
        clearAlert('mensagem-alerta');
        if (nomeArquivo) {
            const tamanhoKB = Math.round(file.size / 1024);
            nomeArquivo.textContent = `Arquivo selecionado: ${file.name} (${tamanhoKB} KB)`;
            nomeArquivo.style.color = '#006d41';
            nomeArquivo.style.fontWeight = '700';
        }
    }

    // Contador de Caracteres no Campo Adicionais
    const textareaAdicionais = document.getElementById('campo-adicionais');
    const contador = document.getElementById('contador-caracteres');
    if (textareaAdicionais && contador) {
        textareaAdicionais.addEventListener('input', () => {
            const len = textareaAdicionais.value.length;
            contador.textContent = `${len} / 500`;
        });
    }

    // Submissão do Formulário
    const form = document.getElementById('form-realizar-inscricao');
    const btnSubmit = document.getElementById('btn-submit-inscricao');

    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            clearAlert('mensagem-alerta');

            if (evento && evento.necessita_comprovante) {
                if (!fileInput.files || fileInput.files.length === 0) {
                    showAlert('mensagem-alerta', 'Por favor, anexe o comprovante exigido para este evento.', 'warning');
                    if (dropzone) dropzone.scrollIntoView({ behavior: 'smooth' });
                    return;
                }
            }

            const formData = new FormData();
            formData.append('evento', eventoId);

            if (fileInput && fileInput.files && fileInput.files[0]) {
                formData.append('comprovante', fileInput.files[0]);
            }

            const adicionaisVal = textareaAdicionais ? textareaAdicionais.value.trim() : '';
            if (adicionaisVal) {
                formData.append('dados_adicionais', JSON.stringify({ necessidades_especiais: adicionaisVal }));
            }

            try {
                if (btnSubmit) {
                    btnSubmit.disabled = true;
                    btnSubmit.style.opacity = '0.7';
                }

                const res = await apiFetch('/inscricoes/', {
                    method: 'POST',
                    body: formData
                });

                const data = await res.json().catch(() => ({}));

                if (res.ok) {
                    if (data.status === 'lista_espera') {
                        showAlert('mensagem-alerta', 'As vagas principais estão preenchidas. Você foi incluído na Lista de Espera!', 'info');
                    } else if (data.status === 'pendente_pagamento') {
                        showAlert('mensagem-alerta', 'Inscrição registrada! Aguardando confirmação do pagamento.', 'info');
                    } else {
                        showAlert('mensagem-alerta', 'Inscrição realizada e confirmada com sucesso!', 'success');
                    }

                    setTimeout(() => {
                        window.location.href = resolveAppUrl('inscricao/minhas-inscricoes/index.html');
                    }, 1500);
                } else {
                    let msg = 'Não foi possível concluir a inscrição.';
                    if (data.detail) msg = data.detail;
                    else if (data.non_field_errors) msg = data.non_field_errors.join(' ');
                    else if (typeof data === 'object') {
                        const erros = Object.entries(data).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`);
                        if (erros.length > 0) msg = erros.join(' | ');
                    }
                    showAlert('mensagem-alerta', msg, 'danger');
                    if (btnSubmit) {
                        btnSubmit.disabled = false;
                        btnSubmit.style.opacity = '1';
                    }
                }
            } catch (err) {
                showAlert('mensagem-alerta', 'Erro de comunicação com o servidor do SGIE.', 'danger');
                if (btnSubmit) {
                    btnSubmit.disabled = false;
                    btnSubmit.style.opacity = '1';
                }
            }
        });
    }
});
