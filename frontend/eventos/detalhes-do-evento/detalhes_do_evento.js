/* SGIE — detalhes_do_evento.js
 * Visualização e gestão completa dos detalhes de um evento.
 */

document.addEventListener('DOMContentLoaded', async () => {
    // 1. Atualizar cabeçalho da aplicação
    atualizarCabecalhoUsuario('eventos');

    // 2. Extrair ID do evento da URL
    const params = new URLSearchParams(window.location.search);
    const eventoId = params.get('id');

    if (!eventoId) {
        mostrarErro('Nenhum evento especificado na URL. Volte à página de eventos.');
        return;
    }

    // 3. Carregar dados do Evento da API
    await carregarDetalhesEvento(eventoId);
});

function formatarDataIso(dataIso) {
    if (!dataIso) return 'A definir';
    const partes = String(dataIso).split('T')[0].split('-');
    if (partes.length < 3) return dataIso;
    const [ano, mes, dia] = partes.map(Number);
    const d = new Date(ano, mes - 1, dia);
    return d.toLocaleDateString('pt-BR', { day: 'numeric', month: 'long', year: 'numeric' });
}

function dataHoraLegivel(isoStr) {
    if (!isoStr) return '—';
    try {
        const d = new Date(isoStr);
        return d.toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
    } catch {
        return isoStr;
    }
}

function obterIniciais(nome) {
    if (!nome) return 'EV';
    const partes = nome.trim().split(/\s+/);
    if (partes.length === 1) return partes[0].slice(0, 2).toUpperCase();
    return (partes[0][0] + partes[partes.length - 1][0]).toUpperCase();
}

async function carregarDetalhesEvento(id) {
    const alertaContainer = document.getElementById('mensagem-alerta');
    if (alertaContainer) alertaContainer.style.display = 'none';

    try {
        const resp = await apiFetch(`/eventos/${id}/`);
        if (!resp.ok) {
            if (resp.status === 404) {
                mostrarErro('O evento solicitado não foi encontrado ou não está disponível.');
            } else {
                mostrarErro('Não foi possível carregar os detalhes do evento no momento.');
            }
            return;
        }

        const evento = await resp.json();
        renderizarPaginaEvento(evento);
    } catch (err) {
        console.error('Erro ao buscar detalhes do evento:', err);
        mostrarErro('Erro de conexão com o servidor do SGIE.');
    }
}

function mostrarErro(mensagem) {
    const alerta = document.getElementById('mensagem-alerta');
    if (alerta) {
        alerta.className = 'alert alert-danger';
        alerta.innerHTML = `<strong>Atenção:</strong> ${mensagem} <br><br><a href="../../index.html" class="btn btn-secondary btn-sm" style="margin-top: 8px;">← Voltar para Explorar Eventos</a>`;
        alerta.style.display = 'block';
    }
    const mainContent = document.querySelector('.detalhes-do-evento__main');
    if (mainContent) {
        const secoes = mainContent.querySelectorAll('section, .detalhes-do-evento__grid-de-conteudo-detail-grid-em-2-colunas');
        secoes.forEach(s => { s.style.display = 'none'; });
    }
}

function renderizarPaginaEvento(ev) {
    const user = getUser();
    const logado = Boolean(user && isAuthenticated());
    const ehRepresentante = Boolean(
        logado && user && user.id && ev.usuario_representante &&
        String(user.id).toLowerCase() === String(ev.usuario_representante).toLowerCase()
    );
    const ehGestor = ehRepresentante;

    // 1. Título da Página
    document.title = `${ev.nome} — SGIE`;

    // 2. Hero Badges
    const badgeStatus = document.getElementById('detalhe-status');
    if (badgeStatus) badgeStatus.textContent = (ev.status_display || ev.status || 'Publicado').toUpperCase();

    const badgeCategoria = document.getElementById('detalhe-categoria');
    if (badgeCategoria) badgeCategoria.textContent = ev.categoria_display || ev.categoria || 'Simpósio';

    const badgeModalidade = document.getElementById('detalhe-modalidade');
    if (badgeModalidade) badgeModalidade.textContent = ev.modalidade_display || ev.modalidade || 'Presencial';

    const badgeVisibilidade = document.getElementById('detalhe-visibilidade');
    if (badgeVisibilidade) badgeVisibilidade.textContent = ev.visibilidade ? `${ev.visibilidade} (Catálogo)` : 'Público';

    const badgePreco = document.getElementById('detalhe-preco');
    if (badgePreco) {
        badgePreco.textContent = ev.e_gratuito ? '100% Gratuito' : (formatarMoeda ? formatarMoeda(ev.preco) : `R$ ${ev.preco}`);
    }

    // 3. Título e Coordenação
    const elNome = document.getElementById('detalhe-nome');
    if (elNome) elNome.textContent = ev.nome;

    const elSubtitulo = document.getElementById('detalhe-subtitulo');
    if (elSubtitulo) {
        const respNome = ev.usuario_representante_nome || 'Coordenação Acadêmica';
        elSubtitulo.textContent = `Coordenação Geral: ${respNome} • SGIE Eventos Institucionais`;
    }

    const elResponsavel = document.getElementById('detalhe-responsavel');
    if (elResponsavel) elResponsavel.textContent = ev.usuario_representante_nome || 'Coordenação Geral';

    const elEmail = document.getElementById('detalhe-email');
    if (elEmail) {
        elEmail.textContent = ev.usuario_representante_email || 'contato@sgie.edu.br';
        elEmail.href = `mailto:${ev.usuario_representante_email || ''}`;
    }

    // 4. Painel de Gestão do Organizador
    const painelGestao = document.getElementById('painel-gestao-organizador');
    const bannerInscricaoPublica = document.getElementById('banner-inscricao-publica');
    const ocupadas = ev.vagas_ocupadas || 0;
    const totalVagas = ev.capacidade || 1;
    const taxaOcupacao = Math.min(100, Math.round((ocupadas / totalVagas) * 100));

    if (ehGestor) {
        if (painelGestao) painelGestao.style.display = 'flex';
        if (bannerInscricaoPublica) bannerInscricaoPublica.style.display = 'none';

        const txtTaxa = document.getElementById('painel-taxa-ocupacao');
        if (txtTaxa) txtTaxa.textContent = `${taxaOcupacao}% Ocupado`;

        const txtVagas = document.getElementById('painel-vagas-descricao');
        if (txtVagas) {
            txtVagas.textContent = `Inscrições: ${ocupadas} vagas preenchidas de ${totalVagas} disponíveis (${taxaOcupacao}%).`;
        }

        // Botão Editar
        const btnEditar = document.getElementById('btn-editar-evento');
        if (btnEditar) {
            btnEditar.onclick = () => {
                window.location.href = `../editar-evento/index.html?id=${ev.id}`;
            };
        }

        // Botão Cancelar
        const btnCancelar = document.getElementById('btn-cancelar-evento');
        if (btnCancelar) {
            if (ev.status === 'Cancelado' || ev.status === 'Finalizado') {
                btnCancelar.style.display = 'none';
            } else {
                btnCancelar.style.display = 'inline-flex';
                btnCancelar.onclick = () => confirmarCancelamento(ev.id);
            }
        }

        // Botão Finalizar / Publicar / Ações de Status
        const btnFinalizar = document.getElementById('btn-finalizar-evento');
        const txtBtnFinalizar = document.getElementById('txt-btn-finalizar');
        if (btnFinalizar && txtBtnFinalizar) {
            if (ev.status === 'Configuração' || ev.status === 'Rascunho') {
                txtBtnFinalizar.textContent = 'Publicar Evento';
                btnFinalizar.onclick = () => mudarStatusEvento(ev.id, 'publicar');
            } else if (ev.status === 'Publicado') {
                txtBtnFinalizar.textContent = 'Abrir Inscrições';
                btnFinalizar.onclick = () => mudarStatusEvento(ev.id, 'abrir-inscricoes');
            } else if (ev.status === 'Inscrições abertas' || ev.status === 'Em realização') {
                txtBtnFinalizar.textContent = 'Finalizar Evento';
                btnFinalizar.onclick = () => mudarStatusEvento(ev.id, 'finalizar');
            } else if (ev.status === 'Finalizado') {
                txtBtnFinalizar.textContent = 'Arquivar Evento';
                btnFinalizar.onclick = () => mudarStatusEvento(ev.id, 'arquivar');
            } else {
                btnFinalizar.style.display = 'none';
            }
        }

        // Botão Consultar Participantes
        const btnParticipantes = document.getElementById('btn-consultar-participantes');
        if (btnParticipantes) {
            btnParticipantes.onclick = () => {
                window.location.href = `../../inscricao/consulta-de-participantes/index.html?evento=${ev.id}`;
            };
        }

    } else {
        // Visitante / Participante (Não é o dono do evento)
        if (painelGestao) painelGestao.style.display = 'none';

        // Desabilita ações restritas ao coordenador/dono
        const btnEditar = document.getElementById('btn-editar-evento');
        if (btnEditar) btnEditar.onclick = null;
        const btnCancelar = document.getElementById('btn-cancelar-evento');
        if (btnCancelar) btnCancelar.onclick = null;
        const btnFinalizar = document.getElementById('btn-finalizar-evento');
        if (btnFinalizar) btnFinalizar.onclick = null;
        const btnParticipantes = document.getElementById('btn-consultar-participantes');
        if (btnParticipantes) btnParticipantes.onclick = null;

        if (bannerInscricaoPublica) {
            bannerInscricaoPublica.style.display = 'flex';
            const btnInscrever = document.getElementById('btn-realizar-inscricao');
            if (btnInscrever) {
                if (ev.status === 'Inscrições abertas' && (ev.vagas_disponiveis === undefined || ev.vagas_disponiveis > 0)) {
                    btnInscrever.href = `../../inscricao/realizar-inscricao/index.html?evento=${ev.id}`;
                    btnInscrever.textContent = 'Realizar Inscrição no Evento';
                    btnInscrever.className = 'btn btn-primary';
                    btnInscrever.style.display = 'inline-flex';
                } else if (ev.vagas_disponiveis === 0) {
                    btnInscrever.href = `../../inscricao/realizar-inscricao/index.html?evento=${ev.id}`;
                    btnInscrever.textContent = 'Entrar na Lista de Espera';
                    btnInscrever.className = 'btn btn-secondary';
                    btnInscrever.style.display = 'inline-flex';
                } else {
                    btnInscrever.style.display = 'none';
                }
            }
        }
    }

    // 5. Descrição do Evento
    const elDescricao = document.getElementById('detalhe-descricao');
    if (elDescricao) {
        elDescricao.textContent = ev.descricao || 'Sem descrição cadastrada.';
    }

    // 6. Submissão de Trabalhos Científicos
    const secaoSubmissao = document.getElementById('secao-submissao');
    const regra = ev.regra_submissao;
    if (regra && regra.aceita_submissao) {
        if (secaoSubmissao) secaoSubmissao.style.display = 'block';
        const txtPrazo = document.getElementById('submissao-prazo-info');
        if (txtPrazo) {
            txtPrazo.textContent = `Período Aberto até ${dataHoraLegivel(regra.data_hora_fim)}`;
        }
    } else {
        if (secaoSubmissao) secaoSubmissao.style.display = 'none';
    }

    // 7. Programação Geral
    const elProgramacao = document.getElementById('detalhe-programacao-container');
    if (elProgramacao) {
        if (ev.programacao_geral && ev.programacao_geral.trim()) {
            const linhas = ev.programacao_geral.trim().split('\n').filter(Boolean);
            elProgramacao.innerHTML = linhas.map(linha => `
                <div class="detalhes-do-evento__item-1" style="margin-bottom: 12px; padding: 12px; background: #f8fafc; border-left: 3px solid #006d41; border-radius: 4px;">
                    <p style="margin: 0; color: #1e293b; font-size: 14px; font-weight: 500;">${linha}</p>
                </div>
            `).join('');
        } else {
            elProgramacao.innerHTML = `<p style="color: #64748b; font-style: italic; margin: 0;">A programação detalhada das sessões será divulgada oportunamente pela comissão organizadora.</p>`;
        }
    }

    // 8. Coluna Lateral: Acesso & Realização
    const elSideData = document.getElementById('sidebar-data');
    if (elSideData) elSideData.textContent = formatarDataIso(ev.data);

    const elSideHorario = document.getElementById('sidebar-horario');
    if (elSideHorario) {
        const hInicio = ev.hora_inicio ? ev.hora_inicio.slice(0, 5) : '—';
        const hFim = ev.hora_fim ? ev.hora_fim.slice(0, 5) : '—';
        elSideHorario.textContent = `${hInicio} às ${hFim} BRT`;
    }

    const elSideLocal = document.getElementById('sidebar-local-designacao');
    if (elSideLocal) elSideLocal.textContent = ev.local || 'Campus Darcy Ribeiro';

    const elSideLocalTipo = document.getElementById('sidebar-local-tipo');
    if (elSideLocalTipo) elSideLocalTipo.textContent = ev.local_tipo || 'Auditório';

    const elSideModalidade = document.getElementById('sidebar-modalidade-texto');
    if (elSideModalidade) elSideModalidade.textContent = ev.modalidade || 'Presencial';

    const elSideVagasTexto = document.getElementById('sidebar-vagas-texto');
    if (elSideVagasTexto) {
        elSideVagasTexto.textContent = `${ocupadas} / ${totalVagas} (${taxaOcupacao}%)`;
    }

    const elSideBarra = document.getElementById('sidebar-vagas-barra');
    if (elSideBarra) {
        elSideBarra.style.width = `${taxaOcupacao}%`;
    }

    const elSideRestantes = document.getElementById('sidebar-vagas-restantes');
    if (elSideRestantes) {
        const restantes = totalVagas - ocupadas;
        elSideRestantes.textContent = restantes > 0
            ? `Restam ${restantes} vagas para confirmação imediata.`
            : 'Capacidade máxima de inscrições atingida.';
    }

    // 9. Equipe Homologada
    const elEquipe = document.getElementById('lista-equipe-organizadora');
    if (elEquipe) {
        if (ev.organizadores && ev.organizadores.length > 0) {
            elEquipe.innerHTML = ev.organizadores.map(org => {
                const nomeOrg = org.usuario_nome || org.usuario_email || 'Organizador';
                const inicial = obterIniciais(nomeOrg);
                const papel = org.papel_display || org.papel || 'Membro da Equipe';
                return `
                    <div class="detalhes-do-evento__membro-1" style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                        <div class="detalhes-do-evento__background-14" style="width: 40px; height: 40px; border-radius: 50%; background: #006d41; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px;">
                            ${inicial}
                        </div>
                        <div class="detalhes-do-evento__container-79">
                            <p style="margin: 0; font-weight: 700; color: #0f172a; font-size: 14px;">${nomeOrg}</p>
                            <p style="margin: 2px 0 0 0; color: #64748b; font-size: 12px;">${papel} ${org.eh_responsavel_principal ? '• Responsável Principal' : ''}</p>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            const respNome = ev.usuario_representante_nome || 'Coordenação Geral';
            const inicial = obterIniciais(respNome);
            elEquipe.innerHTML = `
                <div class="detalhes-do-evento__membro-1" style="display: flex; align-items: center; gap: 12px;">
                    <div class="detalhes-do-evento__background-14" style="width: 40px; height: 40px; border-radius: 50%; background: #006d41; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px;">
                        ${inicial}
                    </div>
                    <div class="detalhes-do-evento__container-79">
                        <p style="margin: 0; font-weight: 700; color: #0f172a; font-size: 14px;">${respNome}</p>
                        <p style="margin: 2px 0 0 0; color: #64748b; font-size: 12px;">Coordenador(a) Geral do Evento</p>
                    </div>
                </div>
            `;
        }
    }
}

async function mudarStatusEvento(id, acao) {
    clearAlert('mensagem-alerta');
    try {
        const resp = await apiFetch(`/eventos/${id}/${acao}/`, { method: 'POST' });
        const dados = await resp.json().catch(() => ({}));
        if (!resp.ok) {
            showAlert('mensagem-alerta', dados.detail || 'Não foi possível atualizar a situação do evento.', 'danger');
            window.scrollTo({ top: 0, behavior: 'smooth' });
            return;
        }
        showAlert('mensagem-alerta', dados.detail || 'Situação do evento atualizada com sucesso!', 'success');
        window.scrollTo({ top: 0, behavior: 'smooth' });
        setTimeout(() => carregarDetalhesEvento(id), 1000);
    } catch {
        showAlert('mensagem-alerta', 'Erro de conexão com o servidor do SGIE.', 'danger');
    }
}

async function confirmarCancelamento(id) {
    const motivo = prompt('Informe a justificativa acadêmica para o cancelamento deste evento:');
    if (motivo === null) return;
    if (!motivo.trim()) {
        alert('O motivo do cancelamento é obrigatório.');
        return;
    }

    try {
        const resp = await apiFetch(`/eventos/${id}/cancelar/`, {
            method: 'POST',
            body: JSON.stringify({ motivo: motivo.trim() }),
        });
        const dados = await resp.json().catch(() => ({}));
        if (!resp.ok) {
            showAlert('mensagem-alerta', dados.detail || 'Não foi possível cancelar o evento.', 'danger');
            window.scrollTo({ top: 0, behavior: 'smooth' });
            return;
        }
        showAlert('mensagem-alerta', 'Evento cancelado com sucesso.', 'success');
        window.scrollTo({ top: 0, behavior: 'smooth' });
        setTimeout(() => carregarDetalhesEvento(id), 1000);
    } catch {
        showAlert('mensagem-alerta', 'Erro de conexão ao cancelar o evento.', 'danger');
    }
}
