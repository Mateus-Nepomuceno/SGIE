document.addEventListener("DOMContentLoaded", () => {
    const formBusca = document.getElementById("form-busca");
    const selectEvento = document.getElementById("select-evento");
    const inputQuery = document.getElementById("input-query");
    const divResultado = document.getElementById("resultado-container");
    const divMensagem = document.getElementById("mensagem-alerta");
    const btnToggleCamera = document.getElementById("btn-toggle-camera");

    let html5QrCode = null;
    let cameraAtiva = false;

	async function carregarEventos() {
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
				selectEvento.appendChild(option);
			});
		} catch (error) {
			showAlert('mensagem-alerta', 'Erro de conexão com o servidor do SGIE.', 'danger');
		}
	}
	carregarEventos()

    async function realizarBusca(query) {
        const eventoId = selectEvento.value;
        if (!eventoId) {
            mostrarMensagem("Por favor, selecione um evento primeiro.", "orange");
            return;
        }

        try {
            const response = await apiFetch(`/credenciamento/buscar/?evento_id=${eventoId}&query=${encodeURIComponent(query)}`);
            const data = await response.json();

            if (response.ok && data.participantes && data.participantes.length > 0) {
                exibirParticipante(data.participantes[0]);
                mostrarMensagem("", "");
            } else {
                divResultado.innerHTML = "";
                mostrarMensagem("Nenhum participante encontrado para este evento.", "red");
            }
        } catch (err) {
            mostrarMensagem("Erro ao conectar com o servidor.", "red");
        }
    }

    if (formBusca) {
        formBusca.addEventListener("submit", (e) => {
            e.preventDefault();
            const query = inputQuery.value.trim();
            if (query) realizarBusca(query);
        });
    }

    if (btnToggleCamera) {
        btnToggleCamera.addEventListener("click", () => {
            if (!selectEvento.value) {
                mostrarMensagem("Selecione um evento antes de ligar a câmara.", "orange");
                return;
            }

            if (cameraAtiva) {
                pararCamera();
            } else {
                iniciarCamera();
            }
        });
    }

    function iniciarCamera() {
        html5QrCode = new Html5Qrcode("reader");
        html5QrCode.start(
            { facingMode: "environment" },
            { fps: 10, qrbox: { width: 220, height: 220 } },
            (decodedText) => {
                realizarBusca(decodedText);
                pararCamera();
            },
            (errorMessage) => {
                // Leitura contínua dos quadros
            }
        ).then(() => {
            cameraAtiva = true;
            btnToggleCamera.textContent = "Parar Câmara";
        }).catch(() => {
            mostrarMensagem("Erro ao acessar a câmara do dispositivo.", "red");
        });
    }

    function pararCamera() {
        if (html5QrCode && cameraAtiva) {
            html5QrCode.stop().then(() => {
                cameraAtiva = false;
                btnToggleCamera.textContent = "Iniciar Câmara";
            });
        }
    }

    function exibirParticipante(p) {
        let acaoHTML = "";

        if (p.status === "CONFIRMADA" && !p.presenca_registrada) {
            acaoHTML = `
                <button type="button" onclick="confirmarPresenca(${p.id})">
                    Confirmar Credenciamento e Registrar Presença
                </button>
            `;
        } else if (p.presenca_registrada) {
            acaoHTML = `<p style="color: blue;"><strong>Presença Já Registrada Anteriormente</strong></p>`;
        } else {
            acaoHTML = `<p style="color: red;"><strong>Inscrição Não Apta para Credenciamento</strong></p>`;
        }

        divResultado.innerHTML = `
            <h3>Dados do Participante</h3>
            <table border="1" cellpadding="6" cellspacing="0">
                <tr>
                    <th>Código Inscrição:</th>
                    <td>#${p.id}</td>
                </tr>
                <tr>
                    <th>Nome:</th>
                    <td>${p.usuario_nome}</td>
                </tr>
                <tr>
                    <th>E-mail:</th>
                    <td>${p.usuario_email}</td>
                </tr>
                <tr>
                    <th>Situação da Inscrição:</th>
                    <td><strong>${p.status}</strong></td>
                </tr>
            </table>
            <br>
            ${acaoHTML}
        `;
    }

    function mostrarMensagem(msg, cor) {
        if (divMensagem) {
            divMensagem.style.color = cor;
            divMensagem.textContent = msg;
        }
    }
});

async function confirmarPresenca(inscricaoId) {
    const csrfToken = getCookie('csrftoken');
    try {
        const response = await apiFetch(`/credenciamento/${inscricaoId}/confirmar/`, {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken,
                "Content-Type": "application/json"
            }
        });
        const data = await response.json();

        if (response.ok) {
            alert(data.success);
            const form = document.getElementById("form-busca");
            if (form) form.dispatchEvent(new Event("submit"));
        } else {
            alert(data.error || data.warning);
        }
    } catch (err) {
        alert("Erro ao processar presença.");
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
