# Refatoração Arquitetural Automatizada — Skill `refactor-arch`

Skill para Claude Code que analisa, audita e refatora projetos de backend para o padrão MVC, de forma agnóstica de linguagem/framework. Construída e validada em 3 projetos reais: um monólito Python/Flask, uma API Node.js/Express, e um projeto Python/Flask parcialmente organizado.

## A) Análise Manual

### Projeto 1 — code-smells-project (Python/Flask)

**Resumo:** API de e-commerce monolítica, 4 arquivos (`app.py`, `controllers.py`, `models.py`, `database.py`), sem separação de camadas real. Concentração extrema de responsabilidades e SQL Injection sistemático.

| # | Severidade | Problema | Localização | Justificativa |
|---|---|---|---|---|
| 1 | **CRITICAL** | SQL Injection sistemático via concatenação de string | `models.py` (múltiplas funções: `get_produto_por_id`, `criar_produto`, `login_usuario`, `buscar_produtos`, etc.) | Quase todas as queries são montadas concatenando strings com input do usuário, sem parametrização. Um payload simples no login (`' OR '1'='1`) bypassa a autenticação. É o problema mais grave do projeto: compromete confidencialidade e integridade de todo o banco. |
| 2 | **CRITICAL** | Senhas armazenadas e comparadas em texto plano | `database.py` (seed), `models.py` (`login_usuario`), `controllers.py` (`listar_usuarios`) | Não há hashing de senha. Além disso, o endpoint de listagem de usuários retorna a senha em claro no JSON — vazamento direto de credenciais para qualquer cliente da API. |
| 3 | **CRITICAL** | Endpoints administrativos sem autenticação (`/admin/reset-db`, `/admin/query`) | `app.py` | Permitem apagar todo o banco ou executar SQL arbitrário sem qualquer verificação de identidade — risco de destruição total dos dados por qualquer requisição HTTP não autenticada. |
| 4 | **HIGH** | Lógica de negócio pesada dentro de Controller/Model | `controllers.py` (notificações por status de pedido), `models.py` (regra de desconto por faixa de faturamento) | Regras de negócio estão espalhadas entre model e controller, sem camada de serviço/domínio. O controller decide regra de negócio em vez de apenas orquestrar — viola separação de responsabilidades do MVC. |
| 5 | **HIGH** | Debug mode habilitado e vazamento de segredo em endpoint público | `app.py` (`DEBUG=True`), `controllers.py` (`health_check` retorna `secret_key`) | Debug mode expõe o debugger interativo do Werkzeug (risco de RCE). O `/health` — que deveria ser um simples liveness check — devolve a `SECRET_KEY` da aplicação na resposta. |
| 6 | **MEDIUM** | N+1 queries em cascata | `models.py` (`get_pedidos_usuario`, `get_todos_pedidos`) | Para cada pedido abre um cursor para buscar itens, e para cada item outro cursor para buscar o produto. Com N pedidos e M itens, gera `1 + N + N*M` queries — degradação severa de performance conforme a base cresce. |
| 7 | **MEDIUM** | Duplicação de lógica de validação | `controllers.py` (`criar_produto` vs `atualizar_produto`) | As mesmas ~10 linhas de validação de campos obrigatórios estão copiadas entre as duas funções, violando DRY — qualquer mudança de regra precisa ser replicada manualmente em dois lugares. |
| 8 | **LOW** | Uso de `print()` para logging | `controllers.py` (diversos pontos) | Em vez de um logger configurável (módulo `logging`), toda a aplicação usa `print()`, dificultando rastreamento e controle de nível de log em produção. |
| 9 | **LOW** | Estado global mutável para conexão de banco | `database.py` (`db_connection` como variável de módulo) | Dificulta testes com mocks e cria acoplamento implícito, em vez de usar injeção de dependência ou factory. |
| 10 | **LOW** | Roteamento sem Blueprints, tudo registrado manualmente no entrypoint | `app.py` (~16 chamadas de `add_url_rule`) | Mistura bootstrap da aplicação com definição de rotas de 3 domínios diferentes (produtos, usuários, pedidos) no mesmo arquivo, sem modularização. |

**Cobertura de severidade:** 3 CRITICAL, 2 HIGH, 2 MEDIUM, 3 LOW — 10 achados no total.

---

### Projeto 2 — ecommerce-api-legacy (Node.js/Express)

**Resumo:** LMS API com fluxo de checkout, 3 arquivos (`app.js`, `AppManager.js`, `utils.js`). Arquitetura de callback hell, God Class centralizando tudo, segurança de pagamento e senha comprometidas.

| # | Severidade | Problema | Localização | Justificativa |
|---|---|---|---|---|
| 1 | **CRITICAL** | Credenciais e chaves de produção hardcoded | `utils.js` (`dbPass`, `paymentGatewayKey`, `smtpUser`) | Chave live de gateway de pagamento e senha de banco em texto plano no código versionado — comprometimento direto de infraestrutura de pagamento real se o repositório vazar. |
| 2 | **CRITICAL** | "Criptografia" de senha falsa e reversível (`badCrypto`) | `utils.js` (função `badCrypto`) | Não é hash — é base64 repetido e truncado, trivialmente reversível. Passa falsa sensação de segurança, o que é pior do que não ter proteção nenhuma. |
| 3 | **HIGH** | God Class: `AppManager` concentra DB, rotas, pagamento, auditoria e cache | `AppManager.js` (classe inteira) | Uma única classe gerencia conexão, rotas HTTP, processamento de pagamento, auditoria e cache — viola completamente separação de responsabilidades. Impossível testar isoladamente. |
| 4 | **HIGH** | Race condition em contadores de callback assíncrono | `AppManager.js` (`/api/admin/financial-report`) | Usa contadores mutáveis compartilhados entre callbacks assíncronos aninhados em vez de `Promise.all`. Sob erro ou concorrência, pode travar a resposta ou disparar `res.json()` mais de uma vez. |
| 5 | **MEDIUM** | Callback hell — pirâmide de 5+ níveis de aninhamento | `AppManager.js` (`/api/checkout`) | Fluxo de checkout aninha múltiplas chamadas de banco em callbacks sucessivos, sem Promises/async-await, dificultando leitura e tratamento de erro consistente. |
| 6 | **MEDIUM** | N+1 (e N×M) queries no relatório financeiro | `AppManager.js` (`/api/admin/financial-report`) | Para cada curso busca matrículas, e para cada matrícula busca usuário e pagamento em queries separadas, sem JOIN — escala mal com o volume de dados. |
| 7 | **MEDIUM** | Validação de pagamento por regra ingênua misturada ao roteamento | `AppManager.js` (`cc.startsWith("4")`) | Aprovação de pagamento decidida pelo primeiro dígito do cartão, sem integração real, validação de formato ou tratamento de exceção — lógica de negócio de pagamento vazando para a camada de rota. |
| 8 | **LOW** | Exclusão de usuário deixa dados órfãos intencionalmente | `AppManager.js` (`DELETE /api/users/:id`) | A própria resposta da API admite que matrículas e pagamentos ficam "sujos" no banco — falta de tratamento de integridade referencial. |
| 9 | **LOW** | Nomes de variáveis abreviados e não descritivos | `AppManager.js` (`u`, `e`, `p`, `cid`, `cc`) | Abreviações prejudicam legibilidade, especialmente em código lidando com dados sensíveis (senha, cartão). |
| 10 | **LOW** | Estado global mutável e código morto (`globalCache`, `totalRevenue`) | `utils.js` | Variáveis de módulo mutáveis exportadas; `totalRevenue` nunca é utilizada em nenhum lugar do código. |

**Cobertura de severidade:** 2 CRITICAL, 2 HIGH, 3 MEDIUM, 3 LOW — 10 achados no total.

---

### Projeto 3 — task-manager-api (Python/Flask, parcialmente organizado)

**Resumo:** API de gerenciamento de tarefas já dividida em `models/`, `routes/`, `services/`, `utils/` — organização de superfície razoável, mas com falhas de segurança graves e duplicação sistemática escondidas sob a estrutura em camadas. Prova que "ter pastas separadas" não é sinônimo de arquitetura correta.

| # | Severidade | Problema | Localização | Justificativa |
|---|---|---|---|---|
| 1 | **CRITICAL** | Token de autenticação falso (não é JWT real) | `routes/user_routes.py` (`login`) | O "token" retornado é a string literal `'fake-jwt-token-' + str(user.id)`, sem assinatura, expiração ou verificação. Qualquer pessoa pode forjar autenticação como qualquer usuário apenas sabendo/adivinhando o ID. É uma falha de autenticação completa do sistema, não um detalhe de implementação. |
| 2 | **CRITICAL** | Credenciais de e-mail (SMTP) hardcoded no código-fonte | `services/notification_service.py` (`__init__`) | Senha de conta de e-mail em texto plano, versionada no repositório — permite envio de e-mail em nome da aplicação (phishing) se vazar. Deveria vir de variável de ambiente (aliás, `python-dotenv` já está no `requirements.txt`, mas não é usado). |
| 3 | **HIGH** | Hashing de senha com MD5 (algoritmo quebrado) | `models/user.py` (`set_password`, `check_password`), usado em `routes/user_routes.py` (`login`) | MD5 é vulnerável a rainbow tables e força bruta em GPU. Toda a autenticação do sistema depende desse hash fraco — deveria usar bcrypt/argon2 com salt. |
| 4 | **HIGH** | N+1 queries sistemático em pelo menos 6 endpoints diferentes | `routes/task_routes.py` (`get_tasks`), `routes/report_routes.py` (`summary_report`, `user_report`, `get_categories`), `routes/user_routes.py` (`get_user`, `get_user_tasks`) | Padrão repetido: busca uma lista e, para cada item, dispara queries adicionais dentro de loop em vez de `join`/eager loading. Não é um caso isolado — é sistemático em toda a camada de rotas, sinal de que falta uma camada de repositório/query otimizada. |
| 5 | **HIGH** | Validação centralizada existe mas nunca é usada (dívida técnica órfã) | `utils/helpers.py` (`process_task_data`) vs. `routes/task_routes.py` (`create_task`, `update_task`) | Existe uma função pronta que reimplementa exatamente as mesmas regras de validação já duplicadas manualmente nas rotas — a equipe sabia da solução certa mas não a adotou. Padrão que a skill deve detectar: "utilitário/serviço existe mas está desconectado do fluxo real". |
| 6 | **MEDIUM** | Duplicação massiva da lógica de "overdue" em 6+ lugares | `models/task.py` (`is_overdue`), reimplementada manualmente em `routes/report_routes.py`, `routes/task_routes.py`, `routes/user_routes.py` | O método já existe no model, mas cada rota reimplementa a mesma lógica de 4 níveis de `if` aninhado manualmente em vez de chamá-lo — uma mudança na regra de atraso exigiria alterar 7 lugares. |
| 7 | **MEDIUM** | `except:` genérico (bare except) engolindo exceções em toda a aplicação | `routes/report_routes.py`, `routes/task_routes.py`, `routes/user_routes.py` (múltiplos endpoints) | Captura qualquer exceção sem logar o erro real, escondendo falhas de programação atrás de mensagens genéricas — dificulta diagnóstico em produção. |
| 8 | **MEDIUM** | Falta de paginação em todos os endpoints de listagem | `routes/task_routes.py`, `routes/user_routes.py`, `routes/report_routes.py` | Todos retornam o dataset completo (`Task.query.all()`) sem `limit`/`offset`. Em produção com grande volume, causa degradação de performance ou timeout — aliás, essa melhoria já está listada como task pendente no próprio `seed.py` ("Adicionar paginação na API"). |
| 9 | **LOW** | `to_dict()` do `User` expõe o hash de senha na serialização | `models/user.py` (`to_dict`) | Qualquer endpoint que serialize um `User` (incluindo a resposta de login) vaza o campo `password` — mesmo hasheado, não deveria estar no payload de saída padrão da API. |
| 10 | **LOW** | Imports não utilizados e utilitários duplicados | `utils/helpers.py` (imports `os`, `json`, `sys`, `math`, `hashlib` nunca usados; `validate_email` duplicada inline em `user_routes.py`) | Sinal de código copiado sem limpeza e de funções utilitárias que existem mas não são adotadas consistentemente pelo time. |

**Cobertura de severidade:** 2 CRITICAL, 3 HIGH, 3 MEDIUM, 2 LOW — 10 achados selecionados (de um total de 26 identificados na análise completa; os demais reforçam os mesmos padrões e foram omitidos por redundância, focando nos de maior impacto arquitetural).

---

## B) Construção da Skill

### Decisões de design

O `SKILL.md` (em `code-smells-project/.claude/skills/refactor-arch/SKILL.md`) foi tratado como um **prompt curto que indexa conhecimento externo**, não como um manual completo. Ele define apenas as 3 fases obrigatórias (Análise → Auditoria → Refatoração), as regras de transição entre elas (principalmente a pausa obrigatória entre Auditoria e Refatoração) e aponta para os arquivos de referência certos em cada fase — sem front-load de conhecimento de domínio. Isso mantém o arquivo em ~120 linhas e deixa o conhecimento pesado (catálogo, playbook) fora do carregamento inicial, sendo lido sob demanda quando a fase correspondente começa.

Os arquivos de referência foram divididos por responsabilidade, seguindo 1:1 as 5 áreas de conhecimento exigidas pelo desafio:

| Arquivo | Fase | Conteúdo |
|---|---|---|
| `analysis-heuristics.md` | 1 | Heurísticas de detecção de stack/framework, mapeamento de fluxo de requisição, taxonomia de "formato de arquitetura" (monolito, fat-controller, fat-model, God Module, MVC vazado) |
| `antipattern-catalog.md` | 2 | Catálogo de anti-patterns com sinal estrutural + severidade |
| `audit-report-template.md` | 2 | Estrutura fixa do relatório, regra de ordenação por severidade, e o prompt de confirmação obrigatório no final |
| `mvc-architecture-guidelines.md` | 3 | Layout MVC alvo (Flask e Express lado a lado) + 3 padrões transversais que "fecham" a refatoração (config centralizada, roteamento em Router/Blueprint, error handling centralizado) |
| `refactoring-playbook.md` | 3 | 20 transformações com código antes/depois, uma por anti-pattern do catálogo |
| `scripts/scan_signals.sh` | 2 | Scanner grep opcional de primeira passagem, usado só para acelerar a busca por candidatos — nunca como fonte de verdade |

Os dois arquivos mais longos (`antipattern-catalog.md` e `refactoring-playbook.md`, ambos > 300 linhas) receberam um sumário com âncoras no topo, para que a skill não precise ler o arquivo inteiro toda vez que só precisa de uma entrada específica.

### Anti-patterns incluídos e por quê

O catálogo final tem **18 anti-patterns** (mínimo exigido: 8), distribuídos como CRITICAL (C1–C6), HIGH (H1–H6), MEDIUM (M1–M4) e LOW (L1–L2). A base foi a lista de problemas reais pedida no enunciado (SQL Injection, credenciais hardcoded, hash fraco, tokens falsos, debug mode, N+1, lógica de negócio em controllers/models, God Class, validação duplicada, callback hell, race conditions, except genérico, falta de paginação), mas o catálogo cresceu em duas rodadas de validação:

1. **Cruzamento com a análise manual dos 3 projetos** (seção A acima): ao comparar o catálogo inicial com os 30 achados documentados manualmente, apareceram 2 lacunas reais — endpoints administrativos sem nenhuma autenticação (agora **C6**) e campos sensíveis (como senha) expostos na serialização de resposta (agora **M4**). O item M1 também foi ampliado de "validação duplicada" para "lógica centralizada duplicada ou ignorada", porque o `task-manager-api` mostrou um padrão mais amplo: uma função utilitária correta que existe mas é ignorada pelos call sites.
2. **Detecção de APIs deprecated (H2)**: exigência explícita do desafio, tratada como categoria própria em vez de exemplo solto — cobre tanto remoção efetiva (`cgi`, `distutils`) quanto deprecação anunciada (`datetime.utcnow()`, `new Buffer()`) nas duas stacks.

### Como garanti que a skill é agnóstica de tecnologia

Cada entrada do catálogo é definida primeiro pelo **sinal estrutural** — o que o código *faz*, não a sintaxe de uma linguagem específica (ex: "uma query é montada concatenando strings com input do usuário" em vez de "uso do operador `+` em Python"). Os exemplos de código em Python/Flask e Node/Express aparecem lado a lado como *ilustração* desse sinal, nunca como definição. O mesmo padrão se repete no `mvc-architecture-guidelines.md` (layout Flask e Express documentados em paralelo, mais uma seção de generalização para outros frameworks como Django, Go e Spring) e no `refactoring-playbook.md` (toda transformação tem "antes/depois" nas duas stacks).

Isso não ficou só na teoria: o scanner `scan_signals.sh` foi testado de fato contra um projeto Node.js real (`ecommerce-api-legacy`), o que expôs falhas de regex específicas de JavaScript.

### Desafios encontrados e como resolvi

- **Regex de detecção de secrets não pegava padrões comuns em JavaScript.** O primeiro regex de C2 exigia palavras completas como "password"/"secret", então não capturava `dbPass` nem `paymentGatewayKey` do projeto Node real. Corrigido com duas estratégias complementares: ampliar a lista de nomes de variável comuns e adicionar uma segunda detecção baseada no **formato do valor** (prefixos conhecidos de chave real, como `pk_live_`, `sk_live_`, `AKIA`), que não depende do nome escolhido para a variável.
- **A skill precisava ser "copiável" de verdade.** Cheguei a considerar link simbólico apontando da pasta de cada projeto para uma cópia única da skill — mas isso quebra se um projeto for copiado/avaliado isoladamente (o link fica pendurado apontando para fora). Optei por cópia física completa em cada projeto, que é o que de fato cumpre o requisito "se ela só funciona em um projeto específico, está acoplada demais".
- **Auto-auditoria da skill revelou conflito com outra skill nativa.** Validando o `SKILL.md` contra 8 critérios de boas práticas (precisão de trigger, modularidade, orçamento de contexto, ausência de instrução suspeita, compatibilidade de stack, conflito com outras skills, independência de GitHub, teste em cenário real), apareceu sobreposição com a skill nativa `security-review` (que audita apenas o diff pendente de um branch). Resolvido reescrevendo a descrição do `SKILL.md` para deixar explícito que o `refactor-arch` audita o **codebase inteiro**, não um diff.
- **Passar no checklist "de olho" não bastou.** Depois da primeira refatoração completa do `code-smells-project`, revalidei contra um checklist mais rígido de Fase 3 e encontrei 3 gaps reais frente às próprias diretrizes da skill: faltava `config.py` centralizando variáveis de ambiente, faltava separação de rotas em Blueprints, e o error handling não era centralizado (17 `try/except` repetidos em vez de 1 handler). Corrigi o código e, mais importante, **realimentei os 3 padrões corrigidos de volta para `mvc-architecture-guidelines.md` e `refactoring-playbook.md`** (novas entradas #19 e #20, com exemplo Flask e Express lado a lado) — para que a próxima execução da skill (inclusive no projeto Node) já aplique esses padrões sem precisar de outra rodada manual de correção.

---

## C) Resultados

**Status: os 3 projetos concluídos** (Análise → Auditoria → confirmação explícita → Refatoração → validação com a aplicação rodando de verdade). Relatórios completos em `reports/audit-project-1.md`, `reports/audit-project-2.md` e `reports/audit-project-3.md`.

### Resumo dos relatórios de auditoria

| Projeto | Stack | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|---|
| 1 — code-smells-project | Python/Flask | 6 | 6 | 2 | 2 | **16** |
| 2 — ecommerce-api-legacy | Node.js/Express | 4 | 4 | 2 | 2 | **12** |
| 3 — task-manager-api | Python/Flask (parcialmente organizado) | 6 | 5 | 4 | 2 | **17** |

O relatório do Projeto 1 verificou explicitamente a detecção de APIs deprecated (H2): nenhuma ocorrência encontrada — as duas dependências (`flask==3.1.1`, `flask-cors==5.0.1`) estão atuais. O relatório do Projeto 2 também verificou H2: nenhuma API deprecated em uso (`express@4.18.2`, `sqlite3@5.1.6`). O relatório do Projeto 3 encontrou 21 ocorrências de `datetime.utcnow()` (deprecated desde Python 3.12) espalhadas por 8 arquivos — a única das três stacks com um achado H2 real — mais 1 ocorrência adicional em `models/category.py` que não constava no relatório original e foi corrigida junto durante a Fase 3, pelo mesmo padrão (assim como um N+1 extra em `get_users` que o scanner também não pegou — ver observações abaixo).

### Comparação antes/depois da estrutura

**Projeto 1 — code-smells-project**
```
Antes                          Depois
app.py                         app.py (rotas + entrypoint + error handlers)
controllers.py (3 domínios)    config.py
models.py (3 domínios)         auth.py (JWT — geração e verificação)
database.py                    controllers/{produtos,usuarios,pedidos,relatorios,admin,health}_controller.py
                                models/{produtos,usuarios,pedidos}_model.py
                                services/{produtos,usuarios,pedidos,relatorios,admin,notificacoes}_service.py
                                routes/{produtos,usuarios,pedidos,relatorios,admin,health}_routes.py
                                validators/produto_validator.py
                                database.py (conexão única, criada no import — sem lock)
```
Monolito de 4 arquivos → split completo por domínio em 5 camadas (routes/controllers/services/models/validators), já que não havia nenhuma separação de responsabilidade para aproveitar. Autenticação/autorização foi resolvida com JWT (`auth.py`), decisão tomada explicitamente antes da Fase 3 por ser a que o catálogo (C6) marca como "decisão do usuário, não da skill".

**Projeto 2 — ecommerce-api-legacy**
```
Antes                          Depois
src/app.js                     src/app.js (entrypoint enxuto)
src/AppManager.js (God Class:  src/config/index.js
  DB + rotas + pagamento +     src/db/database.js (sqlite3 promisificado)
  auditoria + cache)           src/models/{users,courses,enrollments,payments,
src/utils.js (config + cache          auditLogs,reports}.model.js
  + crypto falsa)              src/services/{checkout,reports,users}.service.js
                                src/controllers/{checkout,admin,users}.controller.js
                                src/routes/{checkout,admin,users}.routes.js
                                src/middlewares/{adminAuth,errorHandler}.js
                                src/utils/{logger,errors}.js
```
God Class de 142 linhas (2 arquivos) → 19 arquivos MVC; o relatório financeiro passou de um fan-out de callbacks aninhados com contadores manuais (H6) para uma única query com `JOIN` (H5) — a correção de H5 eliminou H6 como efeito colateral, já que não sobrou nenhum fan-out assíncrono para causar a condição de corrida.

**Projeto 3 — task-manager-api**
```
Antes                          Depois
app.py                         app.py (+ error handlers centralizados)
database.py                    config.py (novo)
models/{user,task,category}.py errors.py (novo — exceções tipadas por status HTTP)
routes/{task,user,report}      database.py
  _routes.py                   models/{user,task,category}.py (M4/H2/C3 corrigidos)
services/                      routes/{task,user,report,category}_routes.py
  notification_service.py      services/{notification,task,user,
utils/helpers.py                      category,report}_service.py
                                utils/auth.py (novo — token assinado e
                                       com expiração via itsdangerous,
                                       decorators login_required/admin_required)
                                utils/helpers.py (agora efetivamente usado)
```
Este projeto **já tinha** `models/routes/services/utils` — a mudança não foi um re-split, foi conectar lógica que já existia e nunca era chamada (ver M1 no relatório), extrair só `categories` para seu próprio blueprint (H3), e adicionar autenticação (que não existia). A autenticação usa `itsdangerous` (já uma dependência transitiva do Flask, sem adicionar biblioteca nova) em vez de JWT — assinatura HMAC + expiração embutida, suficiente para resolver C4/C6 sem inflar `requirements.txt`.

### Checklist de validação preenchido

**Projeto 1 — code-smells-project**

| Fase 1 | Fase 2 | Fase 3 |
|---|---|---|
| [x] Linguagem correta (Python) | [x] Segue template | [x] Estrutura MVC |
| [x] Framework correto (Flask 3.1.1) | [x] Arquivo+linha exatos | [x] Config centralizada, sem hardcoded |
| [x] Domínio correto (e-commerce) | [x] Ordenado por severidade | [x] Models abstraem dados |
| [x] Nº de arquivos condiz (4) | [x] 16 ≥ 5 findings | [x] Routes separadas (Blueprints) |
| | [x] Deprecated verificado | [x] Controllers concentram fluxo |
| | [x] Pausou para confirmação | [x] Error handling centralizado |
| | | [x] Entry point claro |
| | | [x] App inicia sem erro |
| | | [x] Endpoints respondem corretamente |

**Projeto 2 — ecommerce-api-legacy**

| Fase 1 | Fase 2 | Fase 3 |
|---|---|---|
| [x] Linguagem correta (JavaScript/Node) | [x] Segue template | [x] Estrutura MVC |
| [x] Framework correto (Express 4.18.2) | [x] Arquivo+linha exatos | [x] Config centralizada (`dotenv`) |
| [x] Domínio correto (LMS/checkout) | [x] Ordenado por severidade | [x] Models abstraem dados |
| [x] Nº de arquivos condiz (3) | [x] 12 ≥ 5 findings | [x] Routes separadas (`express.Router()`) |
| | [x] Deprecated verificado (nenhuma ocorrência) | [x] Controllers concentram fluxo |
| | [x] Pausou para confirmação | [x] Error handling centralizado (middleware 4-arg) |
| | | [x] Entry point claro |
| | | [x] App inicia sem erro |
| | | [x] Endpoints respondem corretamente |

**Projeto 3 — task-manager-api**

| Fase 1 | Fase 2 | Fase 3 |
|---|---|---|
| [x] Linguagem correta (Python) | [x] Segue template | [x] Estrutura MVC (já existia, reforçada) |
| [x] Framework correto (Flask 3.0.0 + SQLAlchemy) | [x] Arquivo+linha exatos | [x] Config centralizada, sem hardcoded |
| [x] Domínio correto (task manager) | [x] Ordenado por severidade | [x] Models abstraem dados |
| [x] Nº de arquivos condiz (11) | [x] 17 ≥ 5 findings | [x] Routes separadas (categories extraído) |
| | [x] Deprecated verificado (21 ocorrências) | [x] Controllers concentram fluxo (agora via services) |
| | [x] Pausou para confirmação | [x] Error handling centralizado |
| | | [x] Entry point claro |
| | | [x] App inicia sem erro |
| | | [x] Endpoints respondem corretamente |

### Logs de validação (aplicações rodando pós-refatoração)

**Projeto 1:**
```
$ curl http://localhost:5000/health
{"counts":{"pedidos":0,"produtos":10,"usuarios":3},"database":"connected","status":"ok","versao":"1.0.0"}

$ curl -X POST http://localhost:5000/admin/reset-db
{"erro":"Token de autenticação ausente"}   # sem Authorization: Bearer — antes não havia proteção nenhuma

$ curl -X POST http://localhost:5000/login -H 'Content-Type: application/json' -d '{"email":"admin@loja.com","senha":"admin123"}'
{"dados":{"token":"eyJhbGciOiJIUzI1NiIs...","usuario":{"email":"admin@loja.com","id":1,"nome":"Admin","tipo":"admin"}},"mensagem":"Login OK","sucesso":true}

$ curl -X POST http://localhost:5000/admin/reset-db -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
{"mensagem":"Banco de dados resetado","sucesso":true}
```

**Projeto 2:**
```
{"level":30,"time":1789593088798,"pid":246685,"hostname":"...","msg":"Frankenstein LMS rodando na porta 3000..."}

$ curl -X POST http://localhost:3000/api/checkout -H "Content-Type: application/json" \
  -d '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'
{"msg":"Sucesso","enrollment_id":2}

$ curl http://localhost:3000/api/admin/financial-report        # sem x-admin-api-key
→ 401 Não autorizado

$ curl http://localhost:3000/api/admin/financial-report -H "x-admin-api-key: dev-only-admin-key-change-me"
{"report":[{"course":"Clean Architecture","revenue":997,"students":[{"student":"Leonan","paid":997}]},
           {"course":"Docker","revenue":497,"students":[{"student":"Guilherme","paid":497}]}],
 "page":1,"size":20,"total":2}

$ curl -X DELETE http://localhost:3000/api/users/1 -H "x-admin-api-key: dev-only-admin-key-change-me"
→ 204 No Content

$ curl http://localhost:3000/api/admin/financial-report -H "x-admin-api-key: dev-only-admin-key-change-me"
{"report":[{"course":"Clean Architecture","revenue":0,"students":[]},   # matrícula/pagamento do user 1 removidos em cascata, sem lixo órfão
           {"course":"Docker","revenue":497,"students":[{"student":"Guilherme","paid":497}]}],
 "page":1,"size":20,"total":2}
```

**Projeto 3:**
```
2026-09-16 18:39:50 INFO werkzeug: * Serving Flask app 'app' | Debug mode: off

$ curl http://localhost:5000/health
{"status":"ok","timestamp":"2026-09-16 21:39:55.440578+00:00"}

$ curl -X DELETE http://localhost:5000/tasks/999
{"error":"Autenticação necessária"}   # antes: qualquer requisição sem token nenhum deletava a task (C6)

$ curl -X POST http://localhost:5000/login -H "Content-Type: application/json" \
  -d '{"email":"joao@email.com","password":"1234"}'
{"message":"Login realizado com sucesso",
 "token":"eyJ1c2VyX2lkIjoxfQ.aqsMsw.F3HED4MrYi1fNlVPuA3KgusxAbY",   # assinado + expira em 8h, não mais 'fake-jwt-token-1'
 "user":{"active":true,"email":"joao@email.com","id":1,"name":"João Silva","role":"admin"}}   # sem o campo password (M4)

$ curl -X DELETE http://localhost:5000/tasks/10 -H "Authorization: Bearer eyJ1c2VyX2lkIjoxfQ..."
{"message":"Task deletada com sucesso"}

$ curl "http://localhost:5000/tasks?per_page=3"
{"items":[ /* 3 tasks */ ],"page":1,"pages":4,"per_page":3,"total":10}   # paginação (L1) — antes retornava a tabela inteira
```

### Observações sobre o comportamento da skill em stacks diferentes

- **O catálogo agnóstico se sustentou na prática.** Os mesmos IDs de anti-pattern (C2, C3, H5, M2 etc.) foram encontrados e corrigidos nas duas linguagens sem precisar de regras específicas por stack — só a *implementação* da correção mudou (ex: `werkzeug.security` vs. `bcryptjs`; `Blueprint` vs. `express.Router()`).
- **O scanner precisou de ajuste ao encontrar JavaScript real.** O regex de detecção de secrets (C2), validado inicialmente só contra Python, não reconhecia `dbPass`/`paymentGatewayKey` do projeto Node — corrigido adicionando detecção por formato de valor além de nome de variável (ver seção "Desafios encontrados").
- **Projetos "parecidos" (2 em Flask) exigiram refatorações completamente diferentes.** `code-smells-project` precisou de um split estrutural do zero; `task-manager-api` já tinha a estrutura e precisava de outra coisa (conectar lógica órfã, ver M1) — confirma que a skill não aplica uma receita fixa, ela reage ao que encontra em cada Fase 1/2.
- **A camada de serviço em Node ficou mais explícita sobre concorrência.** O H6 (race condition) do projeto 2 desapareceu como efeito colateral da correção de H5 (uma query com `JOIN` elimina o fan-out de callbacks que causava a condição de corrida) — um caso real de duas correções do catálogo se resolverem com uma única mudança.
- **A pausa da Fase 2 disciplinou o escopo da Fase 3 no projeto 3.** A seção "needs a decision" do relatório (`NotificationService` nunca instanciada, `is_admin()` nunca chamado) foi proposital: nenhum dos dois virou mudança de comportamento na Fase 3, só a credencial hardcoded da `NotificationService` foi corrigida (C2), sem ligá-la a nenhuma rota — ligar a notificação por e-mail teria sido uma mudança de comportamento que o usuário nunca confirmou. Pelo mesmo motivo, apenas `DELETE /tasks/<id>` recebeu autenticação (C6), não `POST`/`PUT /tasks` — mesmo sendo inconsistente à primeira vista, foi exatamente o escopo que o relatório da Fase 2 confirmou com o usuário, nem mais nem menos.
- **Achados adicionais do mesmo padrão, fora do relatório original, foram corrigidos durante a Fase 3 — e documentados como tal.** Ao mover `get_users` para o service layer, apareceu um N+1 (`len(u.tasks)` por usuário) que o scanner da Fase 2 não pegou; e `models/category.py` tinha uma ocorrência de `datetime.utcnow()` que não constava na lista original do H2. Os dois foram corrigidos junto por serem instâncias do mesmo anti-pattern já confirmado pelo usuário — mas relatados explicitamente como "extra" no resumo final, em vez de silenciosamente misturados aos 17 achados originais.
- **Correção (pós-entrega):** o achado C6 em `PUT /users/<id>` tinha recomendação composta — exigir autenticação **e** checar se o chamador é admin antes de aceitar mudança no campo `role`. A Fase 3 original aplicou só a autenticação; `admin_required` foi criado em `utils/auth.py` mas nunca chamado dentro de `update_user`, então qualquer usuário autenticado ainda conseguia se autopromover a admin. O achado tinha sido marcado como resolvido por engano — o status correto era **PARTIALLY FIXED**. Corrigido: a rota agora bloqueia com 403 qualquer alteração de `role` por quem não é admin (ver `routes/user_routes.py` e `reports/audit-project-3.md` seção 6 para a verificação com `curl`). Esse gap virou padrão novo no playbook (`refactoring-playbook.md` #21 — autorização por campo sensível) e regra explícita na Fase 3 do `SKILL.md`: um achado com recomendação composta só pode ser "FIXED" quando **todas** as ações foram aplicadas, senão é "PARTIALLY FIXED" com o que falta.

---

## D) Como Executar

### Pré-requisitos

- **Claude Code** instalado e autenticado (`claude` disponível no PATH — foi a ferramenta usada nesta implementação).
- **Python 3.12+** para os dois projetos Flask (`code-smells-project`, `task-manager-api`), com um ambiente virtual por projeto (`python -m venv .venv && .venv/bin/pip install -r requirements.txt`).
- **Node.js** para `ecommerce-api-legacy` (`npm install` dentro da pasta do projeto).
- Variáveis de ambiente por projeto (todos os 3 seguem o mesmo princípio: sem hardcoded, e a ausência de uma variável obrigatória derruba o boot de propósito, em vez de cair num default inseguro):

  | Projeto | Variável | Obrigatória? | Efeito se ausente |
  |---|---|---|---|
  | 1 — code-smells-project | `SECRET_KEY` | Sim | App não sobe (`RuntimeError` explicando como gerar a chave) |
  | 1 — code-smells-project | `JWT_EXP_HOURS` | Não (default `8`) | — |
  | 1 — code-smells-project | `FLASK_DEBUG` | Não (default `false`) | — |
  | 2 — ecommerce-api-legacy | `ADMIN_API_KEY` | Sim | App não sobe (`throw` explícito no `app.js` antes de iniciar o servidor) |
  | 2 — ecommerce-api-legacy | `PAYMENT_GATEWAY_KEY` | Não | Fluxo de checkout segue funcionando (chave mockada, nunca logada) |
  | 3 — task-manager-api | `SECRET_KEY` | Sim | App não sobe (`KeyError` — sem fallback silencioso) |
  | 3 — task-manager-api | `FLASK_DEBUG` | Não (default `false`) | — |
  | 3 — task-manager-api | `TOKEN_EXPIRY_SECONDS` | Não (default `28800`, 8h) | — |
  | 3 — task-manager-api | `DATABASE_URL` | Não (default `sqlite:///tasks.db`) | — |
  | 3 — task-manager-api | `EMAIL_HOST`/`EMAIL_PORT`/`EMAIL_USER`/`EMAIL_PASSWORD` | Não | Notificação por e-mail não é enviada, apenas logada como aviso (`NotificationService` segue não conectada a nenhuma rota — ver seção 4 do relatório) |

### Comandos para executar a skill em cada projeto

```bash
# Projeto 1 — code-smells-project (Python/Flask)
cd code-smells-project
claude "/refactor-arch"

# Projeto 2 — ecommerce-api-legacy (Node.js/Express)
# (copiar a pasta .claude/skills/refactor-arch/ de code-smells-project para cá antes de invocar)
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3 — task-manager-api (Python/Flask, parcialmente organizado)
# (copiar a pasta .claude/skills/refactor-arch/ de code-smells-project para cá antes de invocar)
cd ../task-manager-api
claude "/refactor-arch"
```

A skill sempre executa a Fase 1 (Análise) e a Fase 2 (Auditoria) automaticamente e **para**, pedindo confirmação explícita antes de tocar em qualquer arquivo. Só avança para a Fase 3 (Refatoração) depois que o usuário responde escolhendo o que corrigir (tudo, só CRITICAL/HIGH, achados específicos, ou nada).

### Como validar que a refatoração funcionou

1. **Instalar dependências e subir a aplicação** com as variáveis de ambiente necessárias (ver seção de pré-requisitos acima).
2. **Confirmar que o processo inicia sem erro** — nenhum traceback no log de boot.
3. **Exercitar os endpoints originais via `curl`** (ou o cliente HTTP equivalente do projeto, como o `api.http` do `ecommerce-api-legacy`) — o comportamento observável (status code, formato da resposta) deve ser equivalente ao pré-refatoração para os fluxos que não mudaram de contrato.
4. **Conferir o checklist de validação** (Fase 1: stack/domínio/arquivos; Fase 2: template do relatório, severidade, mínimo de achados; Fase 3: estrutura MVC, config centralizada, rotas separadas, error handling centralizado, boot sem erro, endpoints respondendo) — usado em `code-smells-project` e reaplicável nos outros 2 projetos.

### Ordem de execução seguida neste repositório

1. Análise manual dos 3 projetos (seção A)
2. Criação da skill `refactor-arch` dentro de `code-smells-project/.claude/skills/refactor-arch/`
3. Execução completa (Fase 1 → 2 → 3) no Projeto 1, com iteração sobre gaps encontrados na auto-validação
4. Cópia física da skill para `ecommerce-api-legacy/` e `task-manager-api/`, execução completa em cada um
5. Consolidação dos relatórios em `reports/` e desta documentação
