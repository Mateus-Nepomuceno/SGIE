function dataBRparaISO(valor) {

            const match =
                /^(\d{2})\/(\d{2})\/(\d{4})$/
                    .exec(valor);

            if (!match) {
                return null;
            }


            const dia =
                Number(match[1]);

            const mes =
                Number(match[2]);

            const ano =
                Number(match[3]);


            const data =
                new Date(
                    ano,
                    mes - 1,
                    dia
                );


            const existe =
                data.getFullYear() === ano &&
                data.getMonth() === mes - 1 &&
                data.getDate() === dia;


            if (
                !existe ||
                ano < 1900 ||
                data > new Date()
            ) {
                return null;
            }


            return (
                `${match[3]}-${match[2]}-${match[1]}`
            );
        }


        document.addEventListener(
            "DOMContentLoaded",
            () => {

                if (isAuthenticated()) {

                    window.location.href =
                        "../../index.html";

                    return;
                }


                iniciarToggleSenha();


                document
                    .getElementById("id_cpf")
                    .addEventListener(
                        "input",
                        (event) => {
                            event.target.value =
                                mascaraCPF(
                                    event.target.value
                                );
                        }
                    );


                document
                    .getElementById("id_telefone")
                    .addEventListener(
                        "input",
                        (event) => {
                            event.target.value =
                                mascaraTelefone(
                                    event.target.value
                                );
                        }
                    );


                document
                    .getElementById("id_data_nascimento")
                    .addEventListener(
                        "input",
                        (event) => {
                            event.target.value =
                                mascaraData(
                                    event.target.value
                                );
                        }
                    );


                const form =
                    document.getElementById(
                        "form-cadastro"
                    );

                const btn =
                    document.getElementById(
                        "btn-cadastrar"
                    );


                form.addEventListener(
                    "submit",
                    async (event) => {

                        event.preventDefault();

                        clearAlert(
                            "mensagem-alerta"
                        );


                        const password =
                            document
                                .getElementById("id_password")
                                .value;

                        const confirmacao =
                            document
                                .getElementById("id_password_confirm")
                                .value;

                        const dataISO =
                            dataBRparaISO(
                                document
                                    .getElementById(
                                        "id_data_nascimento"
                                    )
                                    .value
                            );


                        if (!dataISO) {

                            showAlert(
                                "mensagem-alerta",
                                "Informe uma data de nascimento válida no formato dd/mm/aaaa.",
                                "warning"
                            );

                            return;
                        }


                        if (password.length < 8) {

                            showAlert(
                                "mensagem-alerta",
                                "A senha deve ter no mínimo 8 caracteres.",
                                "warning"
                            );

                            return;
                        }


                        if (password !== confirmacao) {

                            showAlert(
                                "mensagem-alerta",
                                "As senhas informadas não coincidem.",
                                "danger"
                            );

                            return;
                        }


                        const payload = {

                            nome_completo:
                                document
                                    .getElementById(
                                        "id_nome_completo"
                                    )
                                    .value
                                    .trim(),

                            cpf:
                                document
                                    .getElementById("id_cpf")
                                    .value
                                    .replace(/\D/g, ""),

                            email:
                                document
                                    .getElementById("id_email")
                                    .value
                                    .trim(),

                            telefone:
                                document
                                    .getElementById("id_telefone")
                                    .value
                                    .trim(),

                            data_nascimento:
                                dataISO,

                            password:
                                password,

                            confirmacao_senha:
                                confirmacao
                        };


                        btn.disabled = true;
                        btn.textContent =
                            "Cadastrando...";


                        try {

                            const response =
                                await fetch(
                                    `${API_BASE_URL}/usuarios/cadastro/`,
                                    {
                                        method: "POST",

                                        headers: {
                                            "Content-Type":
                                                "application/json"
                                        },

                                        body:
                                            JSON.stringify(
                                                payload
                                            )
                                    }
                                );


                            const data =
                                await response.json();


                            if (response.ok) {

                                window.location.href =
                                    "../login/login.html?cadastrado=1";

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
                                "Falha ao conectar com o servidor.",
                                "danger"
                            );

                        } finally {

                            btn.disabled = false;

                            btn.textContent =
                                "Cadastrar";
                        }

                    }
                );

            }
        );
