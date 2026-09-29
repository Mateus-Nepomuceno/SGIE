document.addEventListener("DOMContentLoaded", () => {

            const params =
                new URLSearchParams(
                    window.location.search
                );


            /* ---------------------------------------------------------
               Redirecionamento interno
               --------------------------------------------------------- */

            const redirect =
                params.get("redirect");

            const destino =
                redirect &&
                !/^(https?:)?\/\//i.test(redirect)
                    ? redirect
                    : "../../index.html";


            /* ---------------------------------------------------------
               Usuário já autenticado
               --------------------------------------------------------- */

            if (isAuthenticated()) {
                window.location.href = destino;
                return;
            }


            /* ---------------------------------------------------------
               Mensagens vindas de cadastro/redefinição
               --------------------------------------------------------- */

            if (params.get("cadastrado")) {

                showAlert(
                    "mensagem-alerta",
                    "Cadastro realizado com sucesso! Faça seu login abaixo.",
                    "success"
                );

            } else if (params.get("redefinido")) {

                showAlert(
                    "mensagem-alerta",
                    "Sua senha foi redefinida com sucesso! Faça login com a nova senha.",
                    "success"
                );

            }


            /* ---------------------------------------------------------
               Toggle da senha
               --------------------------------------------------------- */

            iniciarToggleSenha();


            /* ---------------------------------------------------------
               Formulário
               --------------------------------------------------------- */

            const form =
                document.getElementById("form-login");

            const btnEntrar =
                document.getElementById("btn-entrar");


            form.addEventListener(
                "submit",
                async (event) => {

                    event.preventDefault();

                    clearAlert("mensagem-alerta");


                    let identificador =
                        document
                            .getElementById("id_identificador")
                            .value
                            .trim();

                    const password =
                        document
                            .getElementById("id_password")
                            .value;


                    if (!identificador || !password) {

                        showAlert(
                            "mensagem-alerta",
                            "Por favor, informe seu identificador (E-mail ou CPF) e senha.",
                            "warning"
                        );

                        return;
                    }


                    /* CPF formatado -> somente números */
                    if (
                        /^[\d.\-\s]+$/.test(
                            identificador
                        )
                    ) {
                        identificador =
                            identificador.replace(
                                /\D/g,
                                ""
                            );
                    }


                    btnEntrar.disabled = true;
                    btnEntrar.textContent =
                        "Autenticando...";


                    try {

                        const response =
                            await fetch(
                                `${API_BASE_URL}/auth/token/`,
                                {
                                    method: "POST",

                                    headers: {
                                        "Content-Type":
                                            "application/json"
                                    },

                                    body: JSON.stringify({
                                        identificador,
                                        password
                                    })
                                }
                            );


                        let data;
                        try {
                            data = await response.json();
                        } catch (parseError) {
                            const text = await response.text().catch(() => "");
                            data = { detail: text || `Erro ${response.status}: ${response.statusText}` };
                        }

                        if (response.ok) {
                            setAuth(data);
                            window.location.href =
                                destino;
                            return;
                        }

                        showAlert(
                            "mensagem-alerta",
                            data,
                            "danger"
                        );

                    } catch (error) {
                        console.error("Erro na autenticação:", error);
                        showAlert(
                            "mensagem-alerta",
                            "Erro ao conectar à API do SGIE. Verifique se o servidor backend está ativo na porta 8000.",
                            "danger"
                        );
                    } finally {

                        btnEntrar.disabled = false;

                        btnEntrar.textContent =
                            "Entrar";
                    }
                }
            );
        });
