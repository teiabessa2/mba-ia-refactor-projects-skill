# Criação de Skills — Refatoração Arquitetural Automatizada

Ao longo do curso você aprendeu o que são Skills e como elas permitem que um agente de IA atue como um especialista em tarefas específicas. Agora imagine o seguinte cenário: você herdou 3 projetos legados com problemas de arquitetura, segurança e qualidade de código. Revisar e corrigir tudo manualmente levaria dias.

Neste desafio, você vai criar uma Skill que automatiza esse processo — analisando, auditando e refatorando qualquer projeto para o padrão MVC, independente da tecnologia.

## Objetivo

Você deve entregar uma Skill capaz de:

- Analisar uma codebase detectando linguagem, framework e arquitetura atual
- Identificar anti-patterns e code smells, classificando por severidade com arquivo e linha exatos
- Gerar um relatório de auditoria estruturado com todos os achados
- Refatorar o projeto para o padrão MVC (Model-View-Controller), eliminando os problemas encontrados
- Validar o resultado garantindo que a aplicação continua funcionando após as mudanças

A skill deve ser agnóstica de tecnologia, funcionando com diferentes linguagens e frameworks.

## Contexto

### Definição de Severidades

Para padronizar a sua auditoria e os relatórios gerados pela IA, utilize a seguinte escala de classificação baseada em problemas de MVC e SOLID:

- **CRITICAL:** Falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis (ex: credenciais hardcoded, SQL Injection) ou violam completamente a separação de responsabilidades (ex: "God Class" contendo banco de dados, lógicas complexas e roteamento no mesmo arquivo).
- **HIGH:** Fortes violações do padrão MVC ou princípios SOLID que dificultam muito a manutenção e testes (ex: lógicas de negócio pesadas presas dentro de Controllers, forte acoplamento sem Injeção de Dependência, ou uso de estado global mutável em toda a aplicação).
- **MEDIUM:** Problemas de padronização, duplicação de código ou gargalos de performance moderada (ex: Queries N+1 no banco de dados, uso inadequado de middlewares, validações ausentes nas rotas).
- **LOW:** Melhorias de legibilidade, nomenclatura de variáveis ruins, ou "magic numbers" soltos pelo código.

### Exemplo de Uso no CLI

```bash
# Executar a skill no projeto com problemas
cd code-smells-project
claude "/refactor-arch"
```

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:      Flask 3.1.1
Dependencies:  flask-cors
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Monolítica — tudo em 4 arquivos, sem separação de camadas
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~800 lines of code

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 2 | LOW: 3

## Findings

### [CRITICAL] God Class / God Method
File: models.py:1-350
Description: Arquivo único contém toda lógica de negócio, queries SQL, validação e formatação para 4 domínios diferentes.
Impact: Impossível testar em isolamento, qualquer mudança afeta tudo.
Recommendation: Separar em models e controllers por domínio.

### [CRITICAL] Hardcoded Credentials
File: app.py:8
Description: SECRET_KEY hardcoded como 'minha-chave-super-secreta-123'
...

================================
Total: 14 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
```

```
[... refatoração executada ...]

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
src/
├── config/settings.py
├── models/
│   ├── produto_model.py
│   └── usuario_model.py
├── views/
│   └── routes.py
├── controllers/
│   ├── produto_controller.py
│   └── pedido_controller.py
├── middlewares/error_handler.py
└── app.py (composition root)

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================
```

## Tecnologias obrigatórias

- **Ferramenta:** uma das três opções abaixo (não são aceitas outras ferramentas):
  - Claude Code
  - Gemini CLI
  - OpenAI Codex
- **Recurso:** Custom Skills (ou o equivalente na ferramenta escolhida)
- **Formato dos arquivos de referência:** Markdown
- **Projetos-alvo:** Python/Flask (2 projetos) e Node.js/Express (1 projeto) (fornecidos no repositório base)

> **Nota sobre a ferramenta:** Os exemplos deste documento usam o Claude Code (`.claude/skills/`) como referência, pois é a ferramenta utilizada no curso. Se você optar por Gemini CLI ou Codex, adapte o nome da pasta e o comando de invocação conforme a convenção dela — o conceito de skill e a estrutura interna (SKILL.md + arquivos de referência) permanecem os mesmos.

## Requisitos

### 1. Análise Manual dos Projetos

Antes de criar a skill, você deve entender os problemas que ela vai resolver.

**Tarefas:**

- Analisar o projeto `code-smells-project/` (Python/Flask — API de E-commerce)
- Analisar o projeto `ecommerce-api-legacy/` (Node.js/Express — LMS API com fluxo de checkout)
- Analisar o projeto `task-manager-api/` (Python/Flask — API de Task Manager)

Para cada projeto, identificar e documentar no mínimo 5 problemas, incluindo pelo menos:

- 1 de severidade CRITICAL ou HIGH
- 2 de severidade MEDIUM
- 2 de severidade LOW

Documentar os achados na seção "Análise Manual" do seu `README.md`

> **Dica:** Não precisa encontrar todos os problemas — foque nos que têm maior impacto arquitetural. Use os projetos como insumo para entender quais padrões sua skill precisa detectar.

> **Por que 3 projetos?** Dois são Python/Flask (com níveis de organização diferentes) e um é Node.js/Express. Sua skill precisa funcionar nos 3 para provar que é verdadeiramente agnóstica de tecnologia — lidando tanto com código completamente desestruturado quanto com projetos que já possuem alguma separação de camadas.

### 2. Criação da Skill

Agora que você conhece os problemas, crie uma skill que os detecte, gere um relatório de auditoria e corrija automaticamente.

**Tarefas:**

Criar a skill dentro do projeto `code-smells-project/` e implementar o SKILL.md com 3 fases sequenciais:

- **Fase 1 — Análise:** Detectar stack, mapear arquitetura atual, imprimir resumo
- **Fase 2 — Auditoria:** Cruzar código contra catálogo de anti-patterns, gerar relatório, pedir confirmação
- **Fase 3 — Refatoração:** Reestruturar para o padrão MVC, validar que funciona

Criar arquivos de referência em Markdown que forneçam à skill o conhecimento necessário para executar as 3 fases. Os arquivos devem cobrir **obrigatoriamente** as seguintes áreas de conhecimento:

| Área de conhecimento | O que deve conter |
|---|---|
| Análise de projeto | Heurísticas para detecção de linguagem, framework, banco de dados e mapeamento de arquitetura |
| Catálogo de anti-patterns | Anti-patterns com sinais de detecção e classificação de severidade |
| Template de relatório | Formato padronizado do relatório de auditoria (Fase 2) |
| Guidelines de arquitetura | Regras do padrão MVC alvo (camadas Models, Views/Routes e Controllers, responsabilidades de cada uma) |
| Playbook de refatoração | Padrões concretos de transformação para cada anti-pattern (com exemplos de código) |

> **Nota:** Você tem liberdade para organizar os arquivos de referência como preferir — pode usar os nomes e a quantidade de arquivos que fizer sentido para sua skill. O importante é que todas as 5 áreas de conhecimento estejam cobertas. O nome da skill (`refactor-arch`) e o arquivo `SKILL.md` são obrigatórios e não devem ser alterados. O path da skill segue a convenção da ferramenta escolhida (no Claude Code, por exemplo, é `.claude/skills/refactor-arch/`).

**Requisitos da skill:**

- Deve ser agnóstica de tecnologia — deve funcionar corretamente nos 3 projetos fornecidos, independente da stack ou nível de organização
- O catálogo de anti-patterns deve conter no mínimo 8 anti-patterns com severidade distribuída (CRITICAL, HIGH, MEDIUM, LOW)
- O catálogo deve incluir detecção de APIs deprecated — identificar uso de APIs obsoletas e recomendar o equivalente moderno
- O playbook deve ter no mínimo 8 padrões de transformação com exemplos de código antes/depois
- A Fase 2 deve pausar e pedir confirmação antes de modificar qualquer arquivo
- A Fase 3 deve validar o resultado (boot da aplicação + endpoints funcionando)

### 3. Execução da Skill

Execute sua skill nos 3 projetos e valide que ela funciona em todas as stacks.

#### Projeto 1 — code-smells-project (Python/Flask)

Invocar a skill no Claude Code:

```bash
claude "/refactor-arch"
```

> **Nota:** O comando acima é o exemplo com Claude Code. Se você estiver usando Gemini CLI ou Codex, utilize o comando equivalente para invocar uma skill na sua ferramenta.

- Verificar que a Fase 1 detecta corretamente a stack e imprime o resumo
- Verificar que a Fase 2 encontra no mínimo 5 dos problemas documentados na sua análise manual
- Confirmar a execução da Fase 3
- Verificar que a Fase 3:
  - Cria a estrutura de diretórios baseada em MVC
  - A aplicação inicia sem erros
  - Os endpoints originais continuam respondendo
- Salvar o relatório de auditoria (output da Fase 2) em `reports/audit-project-1.md`
- Commitar o código refatorado do projeto no repositório

#### Projeto 2 — ecommerce-api-legacy (Node.js/Express)

Prove que sua skill é reutilizável em outro projeto de backend, mas com stack diferente.

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `ecommerce-api-legacy/`
- Invocar a skill:

```bash
cd ../ecommerce-api-legacy
claude "/refactor-arch"
```

- Verificar que as 3 fases executam corretamente neste projeto
- Salvar o relatório em `reports/audit-project-2.md`
- Commitar o código refatorado do projeto no repositório

#### Projeto 3 — task-manager-api (Python/Flask)

Agora o teste com um projeto Python/Flask que já possui alguma organização de camadas (models, routes, services, utils).

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `task-manager-api/`
- Invocar a skill:

```bash
cd ../task-manager-api
claude "/refactor-arch"
```

- Verificar que:
  - A Fase 1 detecta corretamente Python/Flask como stack e identifica o domínio de Task Manager
  - A Fase 2 identifica problemas mesmo em um projeto parcialmente organizado
  - A Fase 3 melhora a estrutura sem quebrar a aplicação (todos os endpoints devem continuar respondendo)
- Salvar o relatório em `reports/audit-project-3.md`
- Commitar o código refatorado do projeto no repositório

> **Nota:** Este projeto já possui alguma separação de camadas, mas isso não significa que a arquitetura está adequada. A skill deve identificar tanto problemas de código (segurança, performance, qualidade) quanto oportunidades de melhoria arquitetural. Se houver mudanças estruturais necessárias, a skill deve propô-las e executá-las.

#### Validação

Para cada projeto refatorado, valide o seguinte checklist:

```markdown
## Checklist de Validação

### Fase 1 — Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade

### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente
```

> **Dica:** Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

## Entregável

Repositório público no GitHub (fork do repositório base) contendo:

- Skill completa em `.claude/skills/refactor-arch/` (dentro dos 3 projetos)
- Código refatorado dos 3 projetos (resultado da execução da Fase 3, commitado no repositório)
- Relatórios de auditoria em `reports/` (3 arquivos)
- `README.md` atualizado

### Estrutura do repositório

Faça um fork do repositório base contendo os três projetos com code smells.

> **Nota:** A estrutura abaixo usa Claude Code como exemplo (`.claude/skills/`). Se estiver usando outra ferramenta, adapte os caminhos conforme a convenção dela.

```
desafio-skills/
├── README.md                              # Sua documentação
│
├── code-smells-project/                   # Projeto 1 — Python/Flask (API de E-commerce)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← SUA SKILL AQUI
│   │           ├── SKILL.md
│   │           └── (arquivos de referência)
│   ├── app.py
│   ├── controllers.py
│   ├── models.py
│   ├── database.py
│   └── requirements.txt
│
├── ecommerce-api-legacy/                  # Projeto 2 — Node.js/Express (LMS API com checkout)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── src/
│   │   ├── app.js
│   │   ├── AppManager.js
│   │   └── utils.js
│   ├── api.http
│   └── package.json
│
├── task-manager-api/                      # Projeto 3 — Python/Flask (API de Task Manager)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── app.py
│   ├── database.py
│   ├── seed.py
│   ├── requirements.txt
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── utils/
│
└── reports/                               # Relatórios gerados
    ├── audit-project-1.md                 # Saída da Fase 2 no projeto 1
    ├── audit-project-2.md                 # Saída da Fase 2 no projeto 2
    └── audit-project-3.md                 # Saída da Fase 2 no projeto 3
```

**O que você vai criar:**

- `.claude/skills/refactor-arch/` — A skill completa (SKILL.md + arquivos de referência)
- Código refatorado dos 3 projetos — resultado da execução da Fase 3, commitado no repositório
- `reports/audit-project-{1,2,3}.md` — Relatório de auditoria de cada projeto
- `README.md` — Documentação do seu processo

**O que já vem pronto:**

- `code-smells-project/` — API de E-commerce Python/Flask com code smells intencionais
- `ecommerce-api-legacy/` — LMS API Node.js/Express (com fluxo de checkout) e problemas de implementação
- `task-manager-api/` — API de Task Manager Python/Flask com organização parcial e problemas de segurança/qualidade

> **Dica:** Cada projeto contém problemas intencionais de diferentes severidades (CRITICAL, HIGH, MEDIUM, LOW), incluindo falhas de segurança, violações arquiteturais e problemas de qualidade de código. Parte do desafio é identificá-los por conta própria através da análise manual do código.

### README.md deve conter

**A) Seção "Análise Manual":**

- Lista dos problemas identificados manualmente em cada projeto
- Classificação por severidade
- Justificativa de por que cada problema é relevante

**B) Seção "Construção da Skill":**

- Decisões de design: como estruturou o SKILL.md e os arquivos de referência
- Quais anti-patterns incluiu no catálogo e por quê
- Como garantiu que a skill é agnóstica de tecnologia
- Desafios encontrados e como resolveu

**C) Seção "Resultados":**

- Resumo dos relatórios de auditoria dos 3 projetos (quantos findings por severidade em cada)
- Comparação antes/depois da estrutura de cada projeto
- Checklist de validação preenchido para cada projeto
- Screenshots ou logs mostrando as aplicações rodando após refatoração
- Observações sobre como a skill se comportou em stacks diferentes

**D) Seção "Como Executar":**

- Pré-requisitos (a ferramenta escolhida — Claude Code, Gemini CLI ou Codex — instalada e configurada)
- Comandos para executar a skill em cada projeto
- Como validar que a refatoração funcionou

### Ordem de execução sugerida

**1. Analisar os projetos manualmente**

Leia o código dos três projetos e documente os problemas encontrados.

**2. Criar a skill**

Escreva o SKILL.md e os arquivos de referência.

**3. Executar nos 3 projetos**

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

Salve a saída da Fase 2 de cada projeto em `reports/audit-project-{1,2,3}.md`.

**4. Iterar**

Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

## Critérios de Aceite

A skill deve atingir os seguintes mínimos em **todos os 3 projetos**:

| Critério | Requisito |
|---|---|
| Fase 1 detecta stack corretamente | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 encontra >= 5 findings | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 inclui pelo menos 1 CRITICAL ou HIGH | OBRIGATÓRIO (3/3 projetos) |
| Fase 3 aplicação funciona após refatoração | OBRIGATÓRIO (3/3 projetos) |

**IMPORTANTE:** Todos os critérios devem ser atingidos nos 3 projetos, não apenas em um!

> **Sobre o projeto 3 (task-manager-api):** Este projeto já possui alguma organização. "aplicação funciona" significa que a API inicia sem erros e todos os endpoints continuam respondendo corretamente.

## Referências

- [Claude Code: Skills](https://docs.anthropic.com/en/docs/claude-code/skills) — Documentação oficial sobre como criar e estruturar Skills
- [Claude Code: Overview](https://docs.anthropic.com/en/docs/claude-code/overview) — Visão geral do Claude Code e suas capacidades
- [The Complete Guide to Building Skills for Claude (PDF)](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf) — Guia completo da Anthropic sobre construção de Skills
- [Equipping Agents for the Real World with Agent Skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills) — Blog oficial da Anthropic sobre Agent Skills

---

## Dicas Finais

- **Comece pela análise manual** — entender os problemas profundamente é essencial para criar uma skill que os detecte.
- **O SKILL.md é um prompt** — ele instrui o agente sobre o que fazer, enquanto os arquivos de referência fornecem o conhecimento de domínio.
- **Seja específico nos sinais de detecção** — "código ruim" não ajuda; "query SQL dentro de loop for" é acionável.
- **Teste incrementalmente** — não tente criar a skill perfeita de primeira.
- **A skill deve ser copiável** — se ela só funciona em um projeto específico, está acoplada demais. Teste nos 3 projetos para validar.
- **Projetos diferentes exigem adaptação** — a Fase 3 de um projeto já parcialmente organizado não vai ter as mesmas transformações de um monolito. Sua skill deve se adaptar ao contexto.
- **Pedir confirmação na Fase 2 é obrigatório** — o humano deve revisar o relatório antes de qualquer modificação.
- **Consulte as referências do curso** — revise a documentação oficial da ferramenta escolhida e os materiais das aulas para relembrar a estrutura e anatomia de uma skill.

---

## Análise Manual

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

**Cobertura de severidade:** 2 CRITICAL, 3 HIGH, 3 MEDIUM, 2 LOW — 10 achados selecionados (de um total de 26 identificados na análise completa; os demais reforçam os mesmos padrões e foram omitidos por redundância, conforme dica do enunciado de focar nos de maior impacto arquitetural).

---

## Construção da Skill

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

Isso não ficou só na teoria: o scanner `scan_signals.sh` foi testado de fato contra um projeto Node.js real (`ecommerce-api-legacy`), o que expôs falhas de regex específicas de JavaScript (abaixo).

### Desafios encontrados e como resolvi

- **Regex de detecção de secrets não pegava padrões comuns em JavaScript.** O primeiro regex de C2 exigia palavras completas como "password"/"secret", então não capturava `dbPass` nem `paymentGatewayKey` do projeto Node real. Corrigido com duas estratégias complementares: ampliar a lista de nomes de variável comuns e adicionar uma segunda detecção baseada no **formato do valor** (prefixos conhecidos de chave real, como `pk_live_`, `sk_live_`, `AKIA`), que não depende do nome escolhido para a variável.
- **A skill precisava ser "copiável" de verdade.** Cheguei a usar link simbólico apontando da pasta de cada projeto para uma cópia única da skill — mas isso quebra se um projeto for copiado/avaliado isoladamente (o link fica pendurado apontando para fora). Troquei para cópia física completa em cada projeto, que é o que de fato cumpre o requisito "se ela só funciona em um projeto específico, está acoplada demais".
- **Auto-auditoria da skill revelou conflito com outra skill nativa.** Validando a `SKILL.md` contra 8 critérios de boas práticas (precisão de trigger, modularidade, orçamento de contexto, ausência de instrução suspeita, compatibilidade de stack, conflito com outras skills, independência de GitHub, teste em cenário real), apareceu sobreposição com a skill nativa `security-review` (que audita apenas o diff pendente de um branch). Resolvido reescrevendo a descrição do `SKILL.md` para deixar explícito que o `refactor-arch` audita o **codebase inteiro**, não um diff.
- **Passar no checklist "de olho" não bastou.** Depois da primeira refatoração completa do `code-smells-project`, revalidei contra um checklist mais rígido de Fase 3 e encontrei 3 gaps reais frente às próprias diretrizes da skill: faltava `config.py` centralizando variáveis de ambiente, faltava separação de rotas em Blueprints, e o error handling não era centralizado (17 `try/except` repetidos em vez de 1 handler). Corrigi o código e, mais importante, **realimentei os 3 padrões corrigidos de volta para `mvc-architecture-guidelines.md` e `refactoring-playbook.md`** (novas entradas #19 e #20, com exemplo Flask e Express lado a lado) — para que a próxima execução da skill (inclusive no projeto Node) já aplique esses padrões sem precisar de outra rodada manual de correção.

---

## Resultados

**Status atual: Projetos 1 e 2 concluídos (Análise → Auditoria → confirmação explícita → Refatoração → validação com a aplicação rodando de verdade). Projeto 3 ainda pendente de execução.** Relatórios completos em `reports/audit-project-1.md` e `reports/audit-project-2.md`; `audit-project-3.md` será adicionado quando o projeto 3 for refatorado.

### Resumo dos relatórios de auditoria

| Projeto | Stack | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|---|
| 1 — code-smells-project | Python/Flask | 6 | 6 | 2 | 2 | **16** |
| 2 — ecommerce-api-legacy | Node.js/Express | 4 | 4 | 2 | 2 | **12** |
| 3 — task-manager-api | Python/Flask (parcialmente organizado) | — | — | — | — | *pendente* |

O relatório do Projeto 1 verificou explicitamente a detecção de APIs deprecated (H2): nenhuma ocorrência encontrada — as duas dependências (`flask==3.1.1`, `flask-cors==5.0.1`) estão atuais. O relatório do Projeto 2 também verificou H2: nenhuma API deprecated em uso (`express@4.18.2`, `sqlite3@5.1.6`).

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
models/{user,task,category}.py auth.py (novo — JWT real)
routes/{task,user,report}      errors.py (novo)
  _routes.py                   database.py
services/                      models/{user,task,category}.py (M4/H2 corrigidos)
  notification_service.py      routes/{task,user,report,category}_routes.py
utils/helpers.py               services/{notification,task,user,
                                       category,report}_service.py
                                utils/helpers.py (agora efetivamente usado)
```
Este projeto **já tinha** `models/routes/services/utils` — a mudança não foi um re-split, foi conectar lógica que já existia e nunca era chamada (ver M1 no relatório), extrair só `categories` para seu próprio blueprint (H3), e adicionar autenticação (que não existia).

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
| [x] Nº de arquivos condiz (10) | [x] 13 ≥ 5 findings | [x] Routes separadas (categories extraído) |
| | [x] Deprecated verificado (18 ocorrências) | [x] Controllers concentram fluxo (agora via services) |
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
2026-09-15 21:05:18 INFO werkzeug: * Serving Flask app 'app' | Debug mode: off

$ curl -X POST http://localhost:5000/login -d '{"email":"joao@email.com","password":"1234"}'
{"token":"eyJhbGciOiJIUzI1NiIs...","user":{"role":"admin", ...}}   # JWT real, não mais 'fake-jwt-token-1'
```

### Observações sobre o comportamento da skill em stacks diferentes

- **O catálogo agnóstico se sustentou na prática.** Os mesmos IDs de anti-pattern (C2, C3, H5, M2 etc.) foram encontrados e corrigidos nas duas linguagens sem precisar de regras específicas por stack — só a *implementação* da correção mudou (ex: `werkzeug.security` vs. `bcryptjs`; `Blueprint` vs. `express.Router()`).
- **O scanner precisou de ajuste ao encontrar JavaScript real.** O regex de detecção de secrets (C2), validado inicialmente só contra Python, não reconhecia `dbPass`/`paymentGatewayKey` do projeto Node — corrigido adicionando detecção por formato de valor além de nome de variável (ver seção "Desafios encontrados").
- **Projetos "parecidos" (2 em Flask) exigiram refatorações completamente diferentes.** `code-smells-project` precisou de um split estrutural do zero; `task-manager-api` já tinha a estrutura e precisava de outra coisa (conectar lógica órfã, ver M1) — confirma que a skill não aplica uma receita fixa, ela reage ao que encontra em cada Fase 1/2.
- **A camada de serviço em Node ficou mais explícita sobre concorrência.** O H6 (race condition) do projeto 2 desapareceu como efeito colateral da correção de H5 (uma query com `JOIN` elimina o fan-out de callbacks que causava a condição de corrida) — um caso real de duas correções do catálogo se resolverem com uma única mudança.

---

## Como Executar

### Pré-requisitos

- **Claude Code** instalado e autenticado (`claude` disponível no PATH — foi a ferramenta usada nesta implementação).
- **Python 3.12+** para os dois projetos Flask (`code-smells-project`, `task-manager-api`), com um ambiente virtual por projeto (`python -m venv .venv && .venv/bin/pip install -r requirements.txt`).
- **Node.js** para `ecommerce-api-legacy` (`npm install` dentro da pasta do projeto).
- Variáveis de ambiente por projeto (todos os 3 seguem o mesmo princípio do playbook #2 — sem hardcoded, e a ausência de uma variável obrigatória derruba o boot de propósito, em vez de cair num default inseguro):

  | Projeto | Variável | Obrigatória? | Efeito se ausente |
  |---|---|---|---|
  | 1 — code-smells-project | `SECRET_KEY` | Sim | App não sobe (`RuntimeError` explicando como gerar a chave) |
  | 1 — code-smells-project | `JWT_EXP_HOURS` | Não (default `8`) | — |
  | 1 — code-smells-project | `FLASK_DEBUG` | Não (default `false`) | — |
  | 2 — ecommerce-api-legacy | `ADMIN_API_KEY` | Sim | App não sobe (`throw` explícito no `app.js` antes de iniciar o servidor) |
  | 2 — ecommerce-api-legacy | `PAYMENT_GATEWAY_KEY` | Não | Fluxo de checkout segue funcionando (chave mockada, nunca logada) |
  | 3 — task-manager-api | `SECRET_KEY` | Sim | App não sobe (`KeyError`) |
  | 3 — task-manager-api | `FLASK_DEBUG` | Não (default `false`) | — |
  | 3 — task-manager-api | `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASSWORD` | Não | Notificação por e-mail não é enviada, apenas logada como aviso |

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