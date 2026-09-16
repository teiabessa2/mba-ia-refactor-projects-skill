# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"   # cole o valor em SECRET_KEY no .env
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo (senhas já armazenadas com hash).

## Arquitetura

Camadas em `routes/` (registro de rotas por domínio) → `controllers/` (parsing de request e resposta HTTP) → `services/` (regras de negócio e efeitos colaterais) → `models/` (acesso a dados parametrizado). Configuração sensível a ambiente vive em `config.py`, autenticação via JWT em `auth.py`.

## Autenticação

`POST /login` retorna um token JWT (`dados.token`). Envie-o como `Authorization: Bearer <token>` nas rotas protegidas. Usuários com `tipo: "admin"` (ex.: `admin@loja.com` / `admin123` do seed) têm acesso às rotas administrativas (`/usuarios`, `/pedidos` completos, `/relatorios/vendas`, `/admin/reset-db`). Qualquer usuário autenticado pode criar pedidos e ver os próprios.
