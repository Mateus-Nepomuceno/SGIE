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


                const form =
                    document.getElementById(
                        "form-solicitar-recuperacao"
                    );

                const btn =
                    document.getElementById(
                        "btn-solicitar"
                    );

                const inputEmail =
                    document.getElementById(
                        "id_email"
                    );


                inputEmail.value =
                    sessionStorage.getItem(
                        STORAGE_KEY
                    ) || "";


                form.addEventListener(
                    "submit",
                    async (event) => {

                        event.preventDefault();

                        clearAlert(
                            "mensagem-alerta"
                        );


                        const email =
                            inputEmail.value.trim();


                        if (!email) {

                            showAlert(
                                "mensagem-alerta",
                                "Por favor, informe seu e-mail cadastrado.",
                                "warning"
                            );

                            return;
                        }


                        btn.disabled = true;

                        btn.textContent =
                            "Enviando código...";


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

                                sessionStorage.setItem(
                                    STORAGE_KEY,
                                    email
                                );

                                window.location.href =
                                    "../definir-senha/definir_senha.html";

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

                        } finally {

                            btn.disabled = false;

                            btn.textContent =
                                "Enviar Código";
                        }

                    }
                );

            }
        );
