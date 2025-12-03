

    const VerEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    function validateFields() {
        const email = document.getElementById("email");
        const botao = document.getElementById("entrar");

        if (email && botao) {
            botao.disabled = !VerEmail.test(email.value);
        }
    }

    function validarFormulario() {
        const email = document.getElementById("email");

        if (email && !VerEmail.test(email.value)) {
            alert("Por favor, insira um email válido!");
            return false;
        }
        return true;
    }

    function mascaraTelefone(input) {
        let valor = input.value.replace(/\D/g, "");

        if (valor.length > 11) valor = valor.slice(0, 11);

        if (valor.length > 6) {
            input.value = `(${valor.slice(0,2)}) ${valor.slice(2,7)}-${valor.slice(7)}`;
        } else if (valor.length > 2) {
            input.value = `(${valor.slice(0,2)}) ${valor.slice(2)}`;
        } else {
            input.value = valor.replace(/^(\d{0,2})/, "($1");
        }
    }





document.addEventListener("DOMContentLoaded", function () {


    const data = document.getElementById("dataConsulta");
    if (data) {
        const hoje = new Date().toISOString().split("T")[0];
        data.setAttribute("min", hoje);
    }


    window.validarCadastro = function () {
        const s1 = document.getElementById("senha3").value.trim();
        const s2 = document.getElementById("confirmar-senha").value.trim();

        if (s1 !== s2) {
            alert("As senhas não coincidem!");
            return false;
        }
        return true;
    };

    const senhaInput3 = document.getElementById("senha3");
    const toggleSenhaBtn3 = document.getElementById("toggleSenha3");

    if (senhaInput3 && toggleSenhaBtn3) {
        toggleSenhaBtn3.addEventListener("click", () => {
            senhaInput3.type = senhaInput3.type === "password" ? "text" : "password";
            toggleSenhaBtn3.textContent = senhaInput3.type === "text" ? "🙈" : "👁️";
        });
    }

    const senhaInput2 = document.getElementById("confirmar-senha");
    const toggleSenhaBtn2 = document.getElementById("toggleSenha2");

    if (senhaInput2 && toggleSenhaBtn2) {
        toggleSenhaBtn2.addEventListener("click", () => {
            senhaInput2.type = senhaInput2.type === "password" ? "text" : "password";
            toggleSenhaBtn2.textContent = senhaInput2.type === "text" ? "🙈" : "👁️";
        });
    }

    window.validarMedico = function () {
        const crm = document.getElementById("crm")?.value.trim() || "";
        const senha = document.getElementById("senha")?.value.trim() || "";
        return !(crm === "" || senha === "");
    };

    document.addEventListener("input", () => {
        const crm = document.getElementById("crm");
        const senha = document.getElementById("senha");
        const botao = document.getElementById("entrar");

        if (crm && senha && botao) {
            botao.disabled = !(crm.value.trim() && senha.value.trim());
        }
    });

    const senhaInput = document.getElementById("senha");
    const toggleSenhaBtn = document.getElementById("toggleSenha");

    if (senhaInput && toggleSenhaBtn) {
        toggleSenhaBtn.addEventListener("click", () => {
            senhaInput.type = senhaInput.type === "password" ? "text" : "password";
            toggleSenhaBtn.textContent = senhaInput.type === "text" ? "🙈" : "👁️";
        });
    }
});
