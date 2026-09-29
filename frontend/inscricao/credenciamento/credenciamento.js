let html5QrCode = null;
let cameraAtiva = false;
let participanteAtual = null;

document.addEventListener('DOMContentLoaded', () => {
    if (!isAuthenticated()) {
        window.location.href = resolveAppUrl('usuarios/login/login.html');
        return;
    }

    atualizarCabecalhoUsuario('credenciamento');

    const formBusca = document.getElementById('form-busca');
    const selectEvento = document.getElementById('select-evento');
    const inputQuery = document.getElementById('input-query');
    const btnToggleCamera = document.getElementById('btn-toggle-camera');

    if (formBusca) {
        formBusca.addEventListener('submit', (e) => {
            e.preventDefault();
            const q = inputQuery ? inputQuery.value.trim() : '';
            if (q) realizarBusca(q);
        });
    }

    if (selectEvento) {
        selectEvento.addEventListener('change', () => {
            clearAlert('mensagem-alerta');
            const divResultado = document.getElementById('resultado-container');
            if (divResultado) divResultado.style.display = 'none';
            const listaSugestoes = document.getElementById('lista-sugestoes');
            if (listaSugestoes) listaSugestoes.innerHTML = '';
        });
    }

    if (btnToggleCamera) {
        btnToggleCamera.addEventListener('click', () => {
            if (!selectEvento || !selectEvento.value) {
                showAlert('mensagem-alerta', 'Por favor, selecione um evento antes de iniciar a câmera.', 'warning');
                return;
            }

            if (cameraAtiva) {
                pararCamera();
            } else {
                iniciarCamera();
            }
        });
    }

    carregarEventos();
});

async function carregarEventos() {
    const selectEvento = document.getElementById('select-evento');
    if (!selectEvento) return;

    const urlParams = new URLSearchParams(window.location.search);
    const eventoUrlId = urlParams.get('evento');

    try {
        const response = await apiFetch('/eventos/meus-eventos/');
        if (!response.ok) {
            showAlert('mensagem-alerta', 'Não foi possível carregar seus eventos para credenciamento.', 'danger');
            return;
        }

        const eventos = await response.json();

        selectEvento.innerHTML = '<option value="">Selecione um evento para credenciar...</option>';

        eventos.forEach(ev => {
            const option = document.createElement('option');
            option.value = ev.id;
            option.textContent = `${ev.nome} (${formatarData(ev.data)})`;
            selectEvento.appendChild(option);
        });

        if (eventoUrlId && eventos.some(ev => String(ev.id) === String(eventoUrlId))) {
            selectEvento.value = eventoUrlId;
        } else if (eventos.length === 1) {
            selectEvento.value = eventos[0].id;
        }
    } catch (error) {
        showAlert('mensagem-alerta', 'Erro de conexão ao carregar eventos.', 'danger');
    }
}

async function realizarBusca(termo) {
    clearAlert('mensagem-alerta');
    const selectEvento = document.getElementById('select-evento');
    const eventoId = selectEvento ? selectEvento.value : '';

    if (!eventoId) {
        showAlert('mensagem-alerta', 'Por favor, selecione um evento primeiro.', 'warning');
        return;
    }

    // Se o termo contém padrão de código de ingresso SGIE-XXXX-YYYYYY, extrai o ID numérico final
    let queryFinal = termo.trim();
    const matchSgie = queryFinal.match(/SGIE-\d+-(\d+)/i);
    if (matchSgie && matchSgie[1]) {
        queryFinal = String(parseInt(matchSgie[1], 10));
    } else if (queryFinal.startsWith('#')) {
        queryFinal = queryFinal.replace(/^#+/, '');
    }

    try {
        const url = `/credenciamento/buscar/?evento_id=${encodeURIComponent(eventoId)}&query=${encodeURIComponent(queryFinal)}`;
        const response = await apiFetch(url);
        const data = await response.json().catch(() => ({}));

        const divResultado = document.getElementById('resultado-container');
        const listaSugestoes = document.getElementById('lista-sugestoes');

        if (response.ok && data.participantes && data.participantes.length > 0) {
            renderizarSugestoes(data.participantes);
            exibirParticipante(data.participantes[0]);
        } else {
            if (divResultado) divResultado.style.display = 'none';
            if (listaSugestoes) listaSugestoes.innerHTML = '';
            showAlert('mensagem-alerta', 'Nenhum participante encontrado com os dados informados.', 'warning');
        }
    } catch (err) {
        showAlert('mensagem-alerta', 'Erro ao conectar com o servidor.', 'danger');
    }
}

function renderizarSugestoes(participantes) {
    const listaSugestoes = document.getElementById('lista-sugestoes');
    if (!listaSugestoes) return;

    if (participantes.length <= 1) {
        listaSugestoes.innerHTML = '';
        return;
    }

    let itensHtml = '';
    participantes.forEach((p, idx) => {
        const nome = p.usuario_nome || 'Participante';
        const partes = nome.trim().split(/\s+/);
        const iniciais = partes.length > 1
            ? (partes[0][0] + partes[partes.length - 1][0]).toUpperCase()
            : (partes[0] ? partes[0].slice(0, 2).toUpperCase() : 'SG');

        itensHtml += `
            <div class="credenciamento__suggestion-item-${idx === 0 ? '1-selected' : '2'}" onclick="selecionarParticipante(${idx})" style="cursor: pointer; margin-bottom: 8px;">
                <div class="credenciamento__container-30">
                    <div class="credenciamento__background-4"><p class="credenciamento__text-12">${iniciais}</p></div>
                    <div class="credenciamento__container-31">
                        <div class="credenciamento__container-32">
                            <p class="credenciamento__text-13">${nome}</p>
                        </div>
                        <div class="credenciamento__container-33">
                            <p class="credenciamento__text-14">#${p.id} • ${p.usuario_email}</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });

    listaSugestoes.innerHTML = `
        <div style="margin-top: 16px;">
            <p style="font-size: 13px; font-weight: 700; color: #475569; margin-bottom: 8px;">Resultados encontrados (${participantes.length})</p>
            ${itensHtml}
        </div>
    `;

    window.__participantesCache = participantes;
}

function selecionarParticipante(idx) {
    if (window.__participantesCache && window.__participantesCache[idx]) {
        exibirParticipante(window.__participantesCache[idx]);
    }
}

function exibirParticipante(p) {
    participanteAtual = p;
    const divResultado = document.getElementById('resultado-container');
    if (!divResultado) return;

    const nome = p.usuario_nome || p.usuario_email || 'Participante';
    const partes = nome.trim().split(/\s+/);
    const iniciais = partes.length > 1
        ? (partes[0][0] + partes[partes.length - 1][0]).toUpperCase()
        : (partes[0] ? partes[0].slice(0, 2).toUpperCase() : 'SG');

    const statusNorm = String(p.status).toUpperCase();
    const jaCredenciado = Boolean(p.presenca_registrada);

    let statusTexto = 'Inscrição Regular & Confirmada';
    let statusClass = 'credenciamento__background-7';
    let acaoHtml = '';

    if (jaCredenciado) {
        statusTexto = 'Presença Já Registrada';
        statusClass = 'credenciamento__background-border-2';
        acaoHtml = `
            <div style="padding: 16px; background-color: #eff6ff; border: 1.5px solid #bfdbfe; border-radius: 12px; text-align: center; width: 100%;">
                <p style="font-size: 15px; font-weight: 700; color: #1e40af; margin: 0;">Presença já foi confirmada anteriormente para este participante.</p>
            </div>
        `;
    } else if (statusNorm === 'CONFIRMADA') {
        statusTexto = 'Inscrição Regular & Confirmada';
        statusClass = 'credenciamento__background-7';
        acaoHtml = `
            <button type="button" class="credenciamento__button-big-primary-action-button" onclick="confirmarPresenca(${p.id})" style="cursor: pointer; width: 100%; border: none;">
                <span class="credenciamento__button-big-primary-action-button-shadow"></span>
                <span class="credenciamento__overlay">
                    <div class="credenciamento__container-48">
                        <svg viewBox="0 0 21.667 17.767" xmlns="http://www.w3.org/2000/svg" fill="none" class="credenciamento__icon-13" role="img">
                            <path d="M0 17.333 L0 14.3 C0 13.704 0.153 13.144 0.46 12.621 C0.767 12.097 1.192 11.7 1.733 11.429 C2.654 10.96 3.692 10.563 4.848 10.238 C6.003 9.913 7.276 9.75 8.667 9.75 C9.208 9.75 9.736 9.777 10.251 9.831 C10.766 9.885 11.267 9.967 11.754 10.075 L9.858 11.971 C9.66 11.935 9.466 11.917 9.276 11.917 C9.086 11.917 8.883 11.917 8.667 11.917 C7.385 11.917 6.234 12.07 5.214 12.377 C4.193 12.684 3.358 13.018 2.708 13.379 C2.546 13.469 2.415 13.596 2.316 13.758 C2.216 13.921 2.167 14.101 2.167 14.3 L2.167 15.167 L8.938 15.167 L11.104 17.333 L0 17.333 Z M14.679 17.767 L10.942 14.029 L12.458 12.512 L14.679 14.733 L20.15 9.262 L21.667 10.779 L14.679 17.767 Z M8.667 8.667 C7.475 8.667 6.455 8.242 5.606 7.394 C4.758 6.545 4.333 5.525 4.333 4.333 C4.333 3.142 4.758 2.122 5.606 1.273 C6.455 0.424 7.475 0 8.667 0 C9.858 0 10.878 0.424 11.727 1.273 C12.576 2.122 13 3.142 13 4.333 C13 5.525 12.576 6.545 11.727 7.394 C10.878 8.242 9.858 8.667 8.667 8.667 Z" fill="rgb(255, 255, 255)" />
                        </svg>
                    </div>
                </span>
                <span class="credenciamento__container-49">
                    <div class="credenciamento__container-50">
                        <p class="credenciamento__text-22">Confirmar Presença</p>
                    </div>
                    <div class="credenciamento__container-51">
                        <p class="credenciamento__text-23">Liberar credencial & registrar entrada</p>
                    </div>
                </span>
                <span class="credenciamento__margin">
                    <svg viewBox="0 0 14.667 14.667" xmlns="http://www.w3.org/2000/svg" fill="none" class="credenciamento__icon-14" role="img">
                        <path d="M11.16 8.25 L0 8.25 L0 6.417 L11.16 6.417 L6.027 1.283 L7.333 0 L14.667 7.333 L7.333 14.667 L6.027 13.383 L11.16 8.25 Z" fill="rgb(255, 255, 255)" />
                    </svg>
                </span>
            </button>
        `;
    } else {
        statusTexto = `Inscrição ${p.status} (Não Apta)`;
        statusClass = 'credenciamento__background-border-4';
        acaoHtml = `
            <div style="padding: 16px; background-color: #fff1f2; border: 1.5px solid #fecdd3; border-radius: 12px; text-align: center; width: 100%;">
                <p style="font-size: 15px; font-weight: 700; color: #9f1239; margin: 0;">Inscrição não está confirmada para credenciamento.</p>
            </div>
        `;
    }

    divResultado.innerHTML = `
        <div class="credenciamento__result-primary-action-card-identified-participan">
            <header class="credenciamento__header-ribbon-of-result">
                <div class="credenciamento__container-40">
                    <div class="credenciamento__background-6"></div>
                    <div class="credenciamento__container-41">
                        <p class="credenciamento__text-18">PARTICIPANTE IDENTIFICADO</p>
                    </div>
                </div>
                <div class="${statusClass}">
                    <div class="credenciamento__container-42">
                        <svg viewBox="0 0 13.333 13.333" xmlns="http://www.w3.org/2000/svg" fill="none" class="credenciamento__icon-11" role="img">
                            <path d="M5.733 9.733 L10.433 5.033 L9.5 4.1 L5.733 7.867 L3.833 5.967 L2.9 6.9 L5.733 9.733 Z" fill="rgb(0, 109, 65)" />
                        </svg>
                    </div>
                    <p class="credenciamento__text-19">${statusTexto}</p>
                </div>
            </header>
            <div class="credenciamento__gradient-edge-accent-accent-strip"></div>
            <main class="credenciamento__main-action-layout-left-info-right-fast-confirma">
                <div class="credenciamento__left-attendee-detailed-info-cols-1-7">
                    <div class="credenciamento__profile-badge">
                        <div class="credenciamento__background-shadow"><p class="credenciamento__text-20">${iniciais}</p></div>
                        <div class="credenciamento__background-8">
                            <div class="credenciamento__container-43">
                                <svg viewBox="0 0 11.667 11.667" xmlns="http://www.w3.org/2000/svg" fill="none" class="credenciamento__icon-12" role="img">
                                    <path d="M1.167 11.667 C0.846 11.667 0.571 11.552 0.343 11.324 C0.114 11.095 0 10.821 0 10.5 L0 4.083 L4.083 2.917 L5.25 0 L6.417 0 L7.583 2.917 L11.667 4.083 L11.667 10.5 C11.667 11.095 11.095 11.667 10.5 11.667 Z" fill="rgb(255, 255, 255)" />
                                </svg>
                            </div>
                        </div>
                    </div>
                    <ul class="credenciamento__metadata-list">
                        <li class="credenciamento__container-44">
                            <div class="credenciamento__container-45">
                                <div class="credenciamento__heading-3">
                                    <p class="credenciamento__beatriz-mendes-cavalcanti">${nome}</p>
                                </div>
                            </div>
                            <div class="credenciamento__container-46">
                                <p class="credenciamento__beatriz-mendes-universidade-br">${p.usuario_email}</p>
                            </div>
                        </li>
                        <li class="credenciamento__badges-and-academic-metadata-grid">
                            <div class="credenciamento__container-47">
                                <p class="credenciamento__codigo-ingresso">Código Inscrição</p>
                            </div>
                            <p class="credenciamento__text-21">#${p.id}</p>
                        </li>
                    </ul>
                </div>
                <div class="credenciamento__right-primary-action-area-cols-8-12">
                    ${acaoHtml}
                </div>
            </main>
        </div>
    `;

    divResultado.style.display = 'block';
    divResultado.scrollIntoView({ behavior: 'smooth' });
}

async function confirmarPresenca(inscricaoId) {
    clearAlert('mensagem-alerta');
    try {
        const response = await apiFetch(`/credenciamento/${inscricaoId}/confirmar/`, {
            method: 'POST'
        });

        const data = await response.json().catch(() => ({}));

        if (response.ok) {
            showAlert('mensagem-alerta', data.success || 'Presença confirmada e credenciamento registrado com sucesso!', 'success');
            if (participanteAtual && participanteAtual.id === inscricaoId) {
                participanteAtual.presenca_registrada = true;
                exibirParticipante(participanteAtual);
            }
        } else {
            showAlert('mensagem-alerta', data.error || data.warning || 'Não foi possível confirmar a presença.', 'danger');
        }
    } catch (err) {
        showAlert('mensagem-alerta', 'Erro de conexão com o servidor do SGIE.', 'danger');
    }
}

function iniciarCamera() {
    const statusCamera = document.getElementById('status-camera');
    const btnToggle = document.getElementById('btn-toggle-camera');

    if (typeof Html5Qrcode === 'undefined') {
        showAlert('mensagem-alerta', 'Biblioteca leitora de QR Code indisponível.', 'danger');
        return;
    }

    try {
        html5QrCode = new Html5Qrcode('reader');
        html5QrCode.start(
            { facingMode: 'environment' },
            { fps: 10, qrbox: { width: 220, height: 220 } },
            (decodedText) => {
                pararCamera();
                if (statusCamera) statusCamera.textContent = `Código detectado: ${decodedText}`;
                realizarBusca(decodedText);
            },
            () => {
                // Leitura contínua
            }
        ).then(() => {
            cameraAtiva = true;
            if (btnToggle) btnToggle.textContent = 'Parar Câmera';
            if (statusCamera) statusCamera.textContent = 'Câmera ativa • Aponte para o QR Code';
        }).catch(() => {
            cameraAtiva = false;
            showAlert('mensagem-alerta', 'Não foi possível acessar a câmera do dispositivo.', 'warning');
            if (statusCamera) statusCamera.textContent = 'Câmera desativada ou sem permissão';
        });
    } catch (e) {
        showAlert('mensagem-alerta', 'Erro ao inicializar câmera.', 'danger');
    }
}

function pararCamera() {
    const statusCamera = document.getElementById('status-camera');
    const btnToggle = document.getElementById('btn-toggle-camera');

    if (html5QrCode && cameraAtiva) {
        html5QrCode.stop().then(() => {
            cameraAtiva = false;
            if (btnToggle) btnToggle.textContent = 'Abrir Câmera';
            if (statusCamera) statusCamera.textContent = 'Câmera parada';
        }).catch(() => {
            cameraAtiva = false;
        });
    }
}
