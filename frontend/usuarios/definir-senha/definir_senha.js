const STORAGE_KEY =
            "sgie_recuperar_email";


        document.addEventListener(
            "DOMContentLoaded",
            () => {

                if (isAuthenticated()) {

                    window.location.href =
                        "../../index.html";

                    return;
                }


                const email =
                    sessionStorage.getItem(
                        STORAGE_KEY
                    );


                if (!email) {

                    window.location.href =
                        "../recuperar-senha/recuperar_senha.html";

                    return;
                }


                document
                    .getElementById(
                        "email-destino-texto"
                    )
                    .textContent = email;


                iniciarToggleSenha();


                /* =====================================================
                   Código de 6 dígitos
                   ===================================================== */

                const caixas = [
                    ...document.querySelectorAll(
                        ".code-inputs input"
                    )
                ];


                const lerCodigo = () =>
                    caixas
                        .map((caixa) => caixa.value)
                        .join("");


                caixas.forEach(
                    (caixa, index) => {

                        caixa.addEventListener(
                            "input",
                            () => {

                                caixa.value =
                                    caixa.value
                                        .replace(/\D/g, "")
                                        .slice(-1);


                                if (
                                    caixa.value &&
                                    caixas[index + 1]
                                ) {

                                    caixas[index + 1]
                                        .focus();
                                }
                            }
                        );


                        caixa.addEventListener(
                            "keydown",
                            (event) => {

                                if (
                                    event.key ===
                                        "Backspace" &&
                                    !caixa.value &&
                                    caixas[index - 1]
                                ) {

                                    caixas[index - 1]
                                        .focus();
                                }
                            }
                        );


                        caixa.addEventListener(
                            "paste",
                            (event) => {

                                event.preventDefault();


                                const texto =
                                    (
                                        event
                                            .clipboardData
                                            .getData("text") ||
                                        ""
                                    )
                                        .replace(
                                            /\D/g,
                                            ""
                                        )
                                        .slice(
                                            0,
                                            caixas.length
                                        );


                                [...texto].forEach(
                                    (
                                        digito,
                                        indexColado
                                    ) => {

                                        caixas[
                                            indexColado
                                        ].value =
                                            digito;
                                    }
                                );


                                if (texto.length > 0) {

                                    caixas[
                                        Math.min(
                                            texto.length,
                                            caixas.length
                                        ) - 1
                                    ].focus();

                                }

                            }
                        );

                    }
                );


                /* =====================================================
                   Reenviar código
                   ===================================================== */

                const btnReenviar =
                    document.getElementById(
                        "btn-reenviar"
                    );


                function iniciarEspera(
                    segundos = 30
                ) {

                    btnReenviar.disabled = true;

                    btnReenviar.textContent =
                        `Reenviar em ${segundos}s`;


                    const timer =
                        setInterval(
                            () => {

                                segundos--;


                                if (segundos <= 0) {

                                    clearInterval(
                                        timer
                                    );

                                    btnReenviar.disabled =
                                        false;

                                    btnReenviar.textContent =
                                        "Reenviar código agora";

                                    return;
                                }


                                btnReenviar.textContent =
                                    `Reenviar em ${segundos}s`;

                            },
                            1000
                        );
                }


                btnReenviar.addEventListener(
                    "click",
                    async () => {

                        clearAlert(
                            "mensagem-alerta"
                        );


                        try {

                            const response =
                                await fetch(
                                    `${API_BASE_URL}/usuarios/recuperar-senha/`,
                                    {
                                        method: "POST",

                                        headers: {
                                            "Content-Type":
                                                "application/json"
                                        },

                                        body:
                                            JSON.stringify({
                                                email
                                            })
                                    }
                                );


                            const data =
                                await response.json();


                            if (response.ok) {

                                showAlert(
                                    "mensagem-alerta",
                                    "Código reenviado. Verifique seu e-mail.",
                                    "success"
                                );

                                iniciarEspera();

                                return;
                            }


                            showAlert(
                                "mensagem-alerta",
                                data,
                                "danger"
                            );

                        } catch (error) {

                            showAlert(
                                "mensagem-alerta",
                                "Falha ao comunicar com o servidor.",
                                "danger"
                            );
                        }

                    }
                );


                /* =====================================================
                   Redefinir senha
                   ===================================================== */

                const form =
                    document.getElementById(
                        "form-redefinir-senha"
                    );

                const btn =
                    document.getElementById(
                        "btn-redefinir"
                    );


                form.addEventListener(
                    "submit",
                    async (event) => {

                        event.preventDefault();

                        clearAlert(
                            "mensagem-alerta"
                        );


                        const codigo =
                            lerCodigo();

                        const novaSenha =
                            document
                                .getElementById(
                                    "id_nova_senha"
                                )
                                .value;

                        const confirmacao =
                            document
                                .getElementById(
                                    "id_confirmacao_senha"
                                )
                                .value;


                        if (codigo.length !== 6) {

                            showAlert(
                                "mensagem-alerta",
                                "O código deve possuir exatamente 6 dígitos.",
                                "warning"
                            );

                            return;
                        }


                        if (novaSenha.length < 8) {

                            showAlert(
                                "mensagem-alerta",
                                "A senha deve ter no mínimo 8 caracteres.",
                                "warning"
                            );

                            return;
                        }


                        if (
                            novaSenha !==
                            confirmacao
                        ) {

                            showAlert(
                                "mensagem-alerta",
                                "As senhas informadas não coincidem.",
                                "danger"
                            );

                            return;
                        }


                        btn.disabled = true;

                        btn.textContent =
                            "Redefinindo senha...";


                        try {

                            const response =
                                await fetch(
                                    `${API_BASE_URL}/usuarios/redefinir-senha/`,
                                    {
                                        method: "POST",

                                        headers: {
                                            "Content-Type":
                                                "application/json"
                                        },

                                        body:
                                            JSON.stringify({
                                                email,
                                                codigo,
                                                nova_senha:
                                                    novaSenha,
                                                confirmacao_senha:
                                                    confirmacao
                                            })
                                    }
                                );


                            const data =
                                await response.json();


                            if (!response.ok) {

                                showAlert(
                                    "mensagem-alerta",
                                    data,
                                    "danger"
                                );

                                return;
                            }


                            sessionStorage.removeItem(
                                STORAGE_KEY
                            );


                            /*
                             * A API redefine a senha,
                             * mas não cria sessão.
                             *
                             * Por isso fazemos login
                             * automaticamente logo depois.
                             */

                            try {

                                const login =
                                    await fetch(
                                        `${API_BASE_URL}/auth/token/`,
                                        {
                                            method: "POST",

                                            headers: {
                                                "Content-Type":
                                                    "application/json"
                                            },

                                            body:
                                                JSON.stringify({
                                                    identificador:
                                                        email,
                                                    password:
                                                        novaSenha
                                                })
                                        }
                                    );


                                if (login.ok) {

                                    const loginData =
                                        await login.json();

                                    setAuth(loginData);

                                    window.location.href =
                                        "../../index.html";

                                    return;
                                }

                            } catch (error) {
                                /* fallback para login */
                            }


                            window.location.href =
                                "../login/login.html?redefinido=1";

                        } catch (error) {

                            showAlert(
                                "mensagem-alerta",
                                "Erro ao salvar nova senha.",
                                "danger"
                            );

                        } finally {

                            btn.disabled = false;

                            btn.textContent =
                                "Redefinir Senha e Entrar";
                        }

                    }
                );

            }
        );
