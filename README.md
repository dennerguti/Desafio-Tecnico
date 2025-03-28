# Desafio técnico

O Vallorando Cart é um sistema de carrinho de compras integrado com a API FakeStore, permitindo aos usuários:

* Buscar produtos
* Adicionar/remover itens do carrinho
* Exportar/importar o carrinho em formato CSV
* Autenticação segura com JWT

# Funcionalidades

* Autenticação de Usuários
* Busca de Produtos
* Gerenciamento de Carrinho
* Exportação/Importação CSV
* Responsividade

# Tecnologias utilizadas

### Backend

* **Python** (versão 3.11+)
* **Flask** (microframework web)
* **Flask-SQLAlchemy** (ORM para banco de dados)
* **JWT** (JSON Web Tokens para autenticação)
* **Requests** (para consumir a FakeStore API)

### Banco de Dados

* **SQLite** (banco de dados relacional embutido)

### Autenticação

* **JWT** (JSON Web Tokens) com tempo de expiração


# Motivo das decisões técnicas


 **Backend** : Optei por utilizar Python com Flask por sua simplicidade e eficiência no desenvolvimento de aplicações web. Já utilizado em trabalhos prévios da universidade.

 **Banco de Dados** : Escolhi o SQLite como solução de persistência por sua natureza leve e sem necessidade de configuração complexa, Já utilizando em trabalhos prévios da universidade.

 **Frontend** : Por não ter muito conhecimento sobre o Front, acabei utilizando HTML5, CSS3 e JavaScript vanilla, sem frameworks frontend..

 **Autenticação** : Implementei conforme o desafio um sistema baseado em JWT (JSON Web Tokens) que permite autenticação stateless, com tokens que podem ser transmitidos via cookies, headers ou parâmetros.

 **Integração Externa** : A FakeStore API foi escolhida através do desafio como fonte de produtos.


# Configuração e Execução

### Pré-requisitos

* Python 3.7+
* pip

### Instalação

1. Clone o repositório

   ```
   git clone https://github.com/seu-usuario/vallorando-cart.git
   cd vallorando-cart
   ```
2. Crie e ative um ambiente virtual

   ```
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```
3. Instale as dependências

   ```
   pip install -r requirements.txt
   ```
4. Configure as variáveis de ambiente

   ```
   export FLASK_APP=app
   export FLASK_ENV=development  # apenas para desenvolvimento
   ```
5. Execução disponível em run.py:

   ```
   flask run
   ```

   O sistema estará disponível em: [http://localhost:5000](http://localhost:5000/)

### Credenciais Padrão

* Usuário: `admin`
* Senha: `123456`
