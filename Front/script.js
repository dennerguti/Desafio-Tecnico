document.getElementById("loginForm").addEventListener("submit", function(event) {
    event.preventDefault(); // Impede o envio do formulário

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();
    const feedback = document.getElementById("feedback");

    const errorMessages = document.querySelectorAll(".error-message");
    errorMessages.forEach(msg => msg.textContent = ""); // Limpa mensagens de erro anteriores

    let valid = true;

    // Validação do usuário
    if (username === "") {
        errorMessages[0].textContent = "Usuário é obrigatório!";
        valid = false;
    }

    // Validação da senha
    if (password === "") {
        errorMessages[1].textContent = "Senha é obrigatória!";
        valid = false;
    } else if (password.length < 6) {
        errorMessages[1].textContent = "A senha deve ter pelo menos 6 caracteres!";
        valid = false;
    }

    if (!valid) return; // Se houver erro, para a execução

    // Mudar isso depois
    const correctUsername = "admin";
    const correctPassword = "123456";

    if (username === correctUsername && password === correctPassword) {
        feedback.textContent = "Login bem-sucedido!";
        feedback.className = "success";
    } else {
        feedback.textContent = "Usuário ou senha incorretos!";
        feedback.className = "failure";
    }

    feedback.classList.remove("hidden");
});
