/* ==========================================================================
   SGIE — Meu Perfil (usuarios/perfil/perfil.js)

   Depende de: config.js e api.js (apiFetch, getUser, setUser, showAlert,
   clearAlert, mascaras, atualizarCabecalhoUsuario, resolveAppUrl...).
   ========================================================================== */


// ============================================================
// ENDPOINTS
// ------------------------------------------------------------
// ATENÇÃO: confirmar estes caminhos e métodos com o backend.
// Estão concentrados aqui para ajustar em um único lugar.
// ============================================================

const PERFIL_ENDPOINTS = {
    perfil: '/usuarios/perfil/',                    // GET + PATCH (dados pessoais)
    organizador: '/usuarios/perfil/organizador/',   // PATCH (multipart: foto, banner, biografia)
    meusEventos: '/eventos/meus/',                  // GET (eventos sob gestão do usuário)
};

const LIMITE_FOTO_MB = 5;
const LIMITE_BANNER_MB = 10;
const TIPOS_IMAGEM = ['image/jpeg', 'image/png', 'image/webp'];

const estado = {
    foto: null,
    banner: null,
    removerFoto: false,
    fotoUrlOriginal: null,
    nomeExibicao: '',
};


// ============================================================
// UTILITÁRIOS
// ============================================================

function $(id) {
    return document.getElementById(id);
}

function dataBRparaISO(valor) {
    const match = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(valor);

    if (!match) return null;

    const dia = Number(match[1]);
    const mes = Number(match[2]);
    const ano = Number(match[3]);

    const data = new Date(ano, mes - 1, dia);

    const existe =
        data.getFullYear() === ano &&
        data.getMonth() === mes - 1 &&
        data.getDate() === dia;

    if (!existe || ano < 1900 || data > new Date()) return null;

    return `${match[3]}-${match[2]}-${match[1]}`;
}

function mascararCpfExibicao(cpf) {
    const d = String(cpf || '').replace(/\D/g, '');

    if (d.length !== 11) return '—';

    return `***.${d.slice(3, 6)}.${d.slice(6, 9)}-**`;
}

function mascararTelefoneExibicao(telefone) {
    const formatado = mascaraTelefone(telefone);

    if (formatado.length < 14) return formatado || '—';

    return `${formatado.slice(0, -4)}****`;
}

function tempoDesde(dataIso) {
    if (!dataIso) return '';

    const inicio = new Date(dataIso);

    if (isNaN(inicio.getTime())) return '';

    const agora = new Date();

    let meses =
        (agora.getFullYear() - inicio.getFullYear()) * 12 +
        (agora.getMonth() - inicio.getMonth());

    if (agora.getDate() < inicio.getDate()) meses -= 1;

    if (meses < 1) return 'Há menos de 1 mês';

    if (meses < 12) {
        return `Há ${meses} ${meses === 1 ? 'mês' : 'meses'}`;
    }

    const anos = Math.floor(meses / 12);

    return `Há ${anos} ${anos === 1 ? 'ano' : 'anos'}`;
}

function iniciais(nome) {
    const partes = String(nome || '').trim().split(/\s+/).filter(Boolean);

    if (partes.length === 0) return '?';

    const primeira = partes[0][0];
    const ultima = partes.length > 1 ? partes[partes.length - 1][0] : '';

    return (primeira + ultima).toUpperCase();
}

function validarImagem(arquivo, limiteMb) {
    if (!TIPOS_IMAGEM.includes(arquivo.type)) {
        return 'Formato inválido. Use JPG, PNG ou WebP.';
    }

    if (arquivo.size > limiteMb * 1024 * 1024) {
        return `A imagem excede o limite de ${limiteMb}MB.`;
    }

    return null;
}

async function lerErro(response) {
    try {
        return await response.json();
    } catch {
        return 'Não foi possível concluir a operação. Tente novamente.';
    }
}

function rolarParaTopo() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}


// ============================================================
// INICIALIZAÇÃO
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
    if (!isAuthenticated()) {
        window.location.href = resolveAppUrl('usuarios/login/login.html');
        return;
    }

    atualizarCabecalhoUsuario('perfil');

    iniciarMascaras();
    iniciarUploads();
    iniciarContadorBiografia();

    $('form-dados-pessoais').addEventListener('submit', salvarDadosPessoais);
    $('form-organizador').addEventListener('submit', salvarDadosOrganizador);

    carregarPerfil();
    carregarPainelGestao();
});

function iniciarMascaras() {
    $('id_telefone').addEventListener('input', (e) => {
        e.target.value = mascaraTelefone(e.target.value);
    });

    $('id_data_nascimento').addEventListener('input', (e) => {
        e.target.value = mascaraData(e.target.value);
    });
}

function iniciarContadorBiografia() {
    const campo = $('id_biografia');

    const atualizar = () => {
        $('contador-bio').textContent = campo.value.length;
    };

    campo.addEventListener('input', atualizar);
    atualizar();
}


// ============================================================
// CARREGAR PERFIL
// ============================================================

async function carregarPerfil() {
    let dados = null;

    try {
        const response = await apiFetch(PERFIL_ENDPOINTS.perfil);

        if (response.ok) {
            dados = await response.json();
            setUser({ ...getUser(), ...dados });
        } else {
            showAlert(
                'mensagem-alerta',
                'Não foi possível carregar todos os seus dados. Exibindo as informações da sessão.',
                'warning'
            );
        }
    } catch (error) {
        console.error('Falha ao carregar perfil:', error);
        showAlert(
            'mensagem-alerta',
            'Falha ao conectar com o servidor da API. Verifique se o backend está ativo.',
            'danger'
        );
    }

    // Se a API não trouxe perfil_organizador embutido, busca diretamente
    if (dados && !dados.perfil_organizador) {
        try {
            const orgResp = await apiFetch(PERFIL_ENDPOINTS.organizador);
            if (orgResp.ok) {
                const orgData = await orgResp.json();
                dados.perfil_organizador = orgData;
                setUser({ ...getUser(), ...dados });
            }
        } catch (_) {}
    }

    // Se a API falhar, usa o que já está salvo no login.
    preencherPerfil(dados || getUser() || {});
}

function preencherPerfil(u) {
    const org = u.perfil_organizador || u.organizador || {};

    estado.nomeExibicao = u.nome_completo || '';

    // Cabeçalho da página
    $('perfil-subtitulo').textContent =
        [u.nome_completo, u.email].filter(Boolean).join(' • ') || '—';

    // Resumo
    const desde = u.date_joined || u.data_cadastro || u.created_at;
    const tempo = tempoDesde(desde);

    $('resumo-membro-desde').textContent =
        desde
            ? `${formatarData(desde)}${tempo ? ` (${tempo})` : ''}`
            : '—';

    $('resumo-email').textContent = u.email || '—';
    $('resumo-cpf').textContent = mascararCpfExibicao(u.cpf);
    $('resumo-nascimento').textContent = formatarData(u.data_nascimento);
    $('resumo-telefone').textContent = mascararTelefoneExibicao(u.telefone);

    preencherPapelOrganizador(u, org);

    // Formulário de dados pessoais
    $('id_nome_completo').value = u.nome_completo || '';
    $('id_telefone').value = mascaraTelefone(u.telefone);
    $('id_data_nascimento').value = u.data_nascimento
        ? formatarData(u.data_nascimento)
        : '';

    // Formulário de organizador
    $('id_biografia').value = org.biografia || org.bio_do_organizador || org.mini_bio || '';
    $('contador-bio').textContent = $('id_biografia').value.length;

    $('banner-nome').textContent = org.nome_organizacao || u.nome_completo || 'Organizador';

    estado.fotoUrlOriginal = org.foto || org.foto_de_perfil || org.foto_perfil || null;

    definirFoto(estado.fotoUrlOriginal);
    definirBanner(org.banner || org.banner_capa || null);

    const btnOrg = $('btn-salvar-organizador');
    if (btnOrg) {
        const jaPossui = Boolean(org.id || org.bio_do_organizador || org.biografia || org.foto_de_perfil || org.banner);
        btnOrg.textContent = jaPossui ? 'Atualizar Dados de Organizador' : 'Submeter Dados de Organizador';
    }
}

function preencherPapelOrganizador(u, org) {
    const badge = $('resumo-papel');

    const status = String(org.status_homologacao || org.status || '').toLowerCase();
    const temSolicitacao = Boolean(org.id || org.bio_do_organizador || org.biografia || org.foto_de_perfil || org.foto || org.banner);

    badge.className = 'badge';

    if (u.is_organizador || u.organizador === true || org.homologado === true || status === 'homologado' || status === 'aprovado') {
        badge.classList.add('badge-success');
        badge.textContent = 'Homologado ✓';
    } else if (temSolicitacao || status === 'pendente' || status === 'em_analise') {
        badge.classList.add('badge-warning');
        badge.textContent = 'Em análise';
    } else {
        badge.classList.add('badge-neutral');
        badge.textContent = 'Não solicitado';
    }
}


// ============================================================
// FOTO E BANNER
// ============================================================

function definirFoto(url) {
    const img = $('foto-preview');
    const iniciaisEl = $('foto-iniciais');
    const check = $('foto-check');
    const badge = $('foto-badge');

    if (url) {
        img.src = url;
        img.hidden = false;
        iniciaisEl.hidden = true;
        check.hidden = false;
        badge.hidden = false;
    } else {
        img.removeAttribute('src');
        img.hidden = true;
        iniciaisEl.hidden = false;
        iniciaisEl.textContent = iniciais(estado.nomeExibicao);
        check.hidden = true;
        badge.hidden = true;
    }
}

function definirBanner(url) {
    const img = $('banner-preview');

    if (url) {
        img.src = url;
        img.hidden = false;
    } else {
        img.removeAttribute('src');
        img.hidden = true;
    }
}

function iniciarUploads() {
    $('input-foto').addEventListener('change', (e) => {
        const arquivo = e.target.files[0];

        if (!arquivo) return;

        const erro = validarImagem(arquivo, LIMITE_FOTO_MB);

        if (erro) {
            showAlert('mensagem-alerta', erro, 'warning');
            e.target.value = '';
            return;
        }

        clearAlert('mensagem-alerta');

        estado.foto = arquivo;
        estado.removerFoto = false;

        definirFoto(URL.createObjectURL(arquivo));
    });

    $('btn-remover-foto').addEventListener('click', () => {
        estado.foto = null;
        estado.removerFoto = Boolean(estado.fotoUrlOriginal);

        $('input-foto').value = '';

        definirFoto(null);
    });

    $('input-banner').addEventListener('change', (e) => {
        const arquivo = e.target.files[0];

        if (!arquivo) return;

        const erro = validarImagem(arquivo, LIMITE_BANNER_MB);

        if (erro) {
            showAlert('mensagem-alerta', erro, 'warning');
            e.target.value = '';
            return;
        }

        clearAlert('mensagem-alerta');

        estado.banner = arquivo;

        definirBanner(URL.createObjectURL(arquivo));
    });
}


// ============================================================
// SALVAR DADOS PESSOAIS
// ============================================================

async function salvarDadosPessoais(event) {
    event.preventDefault();

    clearAlert('mensagem-alerta');

    const nome = $('id_nome_completo').value.trim();
    const telefone = $('id_telefone').value.trim();
    const dataISO = dataBRparaISO($('id_data_nascimento').value);

    if (!nome) {
        showAlert('mensagem-alerta', 'Informe seu nome completo.', 'warning');
        rolarParaTopo();
        return;
    }

    if (telefone.replace(/\D/g, '').length < 10) {
        showAlert('mensagem-alerta', 'Informe um telefone válido com DDD.', 'warning');
        rolarParaTopo();
        return;
    }

    if (!dataISO) {
        showAlert(
            'mensagem-alerta',
            'Informe uma data de nascimento válida no formato dd/mm/aaaa.',
            'warning'
        );
        rolarParaTopo();
        return;
    }

    const btn = $('btn-salvar-pessoais');
    const textoOriginal = btn.textContent;

    btn.disabled = true;
    btn.textContent = 'Salvando...';

    try {
        const response = await apiFetch(PERFIL_ENDPOINTS.perfil, {
            method: 'PATCH',
            body: JSON.stringify({
                nome_completo: nome,
                telefone: telefone,
                data_nascimento: dataISO,
            }),
        });

        if (response.ok) {
            const atualizado = await response.json().catch(() => ({}));

            const usuario = {
                ...getUser(),
                ...atualizado,
                nome_completo: atualizado.nome_completo || nome,
            };

            setUser(usuario);

            atualizarCabecalhoUsuario('perfil');
            preencherPerfil({ ...usuario, telefone, data_nascimento: dataISO });

            showAlert('mensagem-alerta', 'Dados pessoais atualizados com sucesso.', 'success');
        } else {
            showAlert('mensagem-alerta', await lerErro(response), 'danger');
        }
    } catch (error) {
        console.error('Falha ao salvar dados pessoais:', error);
        showAlert('mensagem-alerta', 'Falha ao conectar com o servidor da API. Verifique se o backend está ativo.', 'danger');
    } finally {
        btn.disabled = false;
        btn.textContent = textoOriginal;

        rolarParaTopo();
    }
}


// ============================================================
// SALVAR DADOS DO ORGANIZADOR
// ============================================================

async function salvarDadosOrganizador(event) {
    event.preventDefault();

    clearAlert('mensagem-alerta');

    const biografia = $('id_biografia').value.trim();

    const formData = new FormData();

    formData.append('biografia', biografia);
    formData.append('bio_do_organizador', biografia);

    if (estado.foto) {
        formData.append('foto', estado.foto);
        formData.append('foto_de_perfil', estado.foto);
    }
    if (estado.banner) formData.append('banner', estado.banner);
    if (estado.removerFoto) formData.append('remover_foto', 'true');

    const btn = $('btn-salvar-organizador');
    const textoOriginal = btn.textContent;

    btn.disabled = true;
    btn.textContent = 'Enviando...';

    try {
        const response = await apiFetch(PERFIL_ENDPOINTS.organizador, {
            method: 'PATCH',
            body: formData,
        });

        if (response.ok) {
            const atualizado = await response.json().catch(() => ({}));

            const usuarioAtual = getUser() || {};
            setUser({
                ...usuarioAtual,
                perfil_organizador: {
                    ...(usuarioAtual.perfil_organizador || {}),
                    ...atualizado,
                },
            });

            estado.foto = null;
            estado.banner = null;
            estado.removerFoto = false;

            await carregarPerfil();

            showAlert(
                'mensagem-alerta',
                'Dados de organizador enviados com sucesso! Sua solicitação está em análise e aguarda homologação do administrador.',
                'success'
            );
        } else {
            showAlert('mensagem-alerta', await lerErro(response), 'danger');
        }
    } catch (error) {
        console.error('Falha ao salvar dados de organizador:', error);
        showAlert('mensagem-alerta', 'Falha ao conectar com o servidor da API. Verifique se o backend está ativo.', 'danger');
    } finally {
        btn.disabled = false;
        btn.textContent = textoOriginal;

        rolarParaTopo();
    }
}


// ============================================================
// PAINEL DE GESTÃO
// ============================================================

async function carregarPainelGestao() {
    const total = $('painel-total');
    const descricao = $('painel-descricao');

    try {
        const response = await apiFetch(PERFIL_ENDPOINTS.meusEventos);

        if (!response.ok) throw new Error('resposta inválida');

        const data = await response.json();
        const lista = Array.isArray(data) ? data : (data.results || []);

        const quantidade = typeof data.count === 'number'
            ? data.count
            : lista.length;

        total.textContent = String(quantidade).padStart(2, '0');

        descricao.textContent =
            quantidade === 0
                ? 'Você ainda não possui eventos sob sua gestão.'
                : `${quantidade} ${quantidade === 1 ? 'evento sob sua coordenação' : 'eventos sob sua coordenação'} no SGIE.`;
    } catch (error) {
        total.textContent = '—';
        descricao.textContent = 'Não foi possível carregar seus eventos agora.';
    }
}
