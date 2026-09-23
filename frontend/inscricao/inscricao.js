document.addEventListener('DOMContentLoaded', async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const eventoId = urlParams.get('evento');
    document.getElementById('evento_id').value = eventoId;

    const form = document.getElementById('form-inscricao');
    const selectCategoria = document.getElementById('categoria');
    const divComprovante = document.getElementById('campo-comprovante');

    try {
        const response = await apiFetch(`/eventos/${eventoId}/`);
        const evento = await response.json();

        document.getElementById('evento-titulo').innerText = evento.nome;
        document.getElementById('evento-detalhes').innerText =
            `${evento.vagas_disponiveis} vagas restantes - ${evento.e_gratuito ? 'Gratuito' : 'Pago'}`;
    } catch (error) {
        alert("Erro ao carregar os dados do evento.");
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(form);

        const dadosAdicionais = formData.get('adicionais')
        formData.append('dados_adicionais', JSON.stringify(dadosAdicionais));
        formData.delete('adicionais');

        const token = localStorage.getItem('token');

        try {
            const res = await apiFetch('/inscricao/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });

            const data = await res.json();

            if (res.ok) {
                if (data.status === 'lista_espera') {
                    alert('As vagas acabaram, mas você foi adicionado à lista de espera!');
                } else if (data.status === 'pendente_pagamento') {
                    alert('Inscrição registrada! Redirecionando para pagamento...');
                    window.location.href = '/usuarios/perfil.html';
                } else {
                    alert('Inscrição confirmada com sucesso!');
                    window.location.href = '/usuarios/perfil.html';
                }
            } else {
                alert('Erro ao realizar inscrição: ' + JSON.stringify(data));
            }
        } catch (error) {
            alert("Erro de conexão com o servidor.");
        }
    });
});
