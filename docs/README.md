# Gestão de Imóveis — como rodar o sistema

Sistema de gerenciamento de imóveis e aluguéis.
Backend: Django + DRF (`backend/`) · Frontend: Next.js (`frontend/`) ·
Banco: PostgreSQL via Docker (`docker-compose.yml`).

## Jeito mais fácil (Windows)

**Duplo clique em `iniciar-sistema.bat`** — ele abre o Docker, o banco, o
backend (:8000) e o frontend (:3000) e já abre o navegador no sistema.
Para encerrar, feche as duas janelas de terminal que ele abrir.

## Rodar tudo manualmente (Docker Desktop aberto)

```bash
docker compose up -d db          # PostgreSQL (porta 5432)
# em outro terminal, dentro de backend/:
export DB_NAME=arkhe DB_USER=postgres DB_PASSWORD=postgres DB_HOST=localhost DB_PORT=5432
./venv/Scripts/python manage.py migrate
./venv/Scripts/python manage.py seed_initial_data   # plano de contas padrão
./venv/Scripts/python manage.py runserver           # API em http://localhost:8000
```

Frontend (em `frontend/`): `npm run dev` → http://localhost:3000

Ou, com Docker para tudo: `docker compose up --build` (API :8000, frontend :3000).

## Testes (não precisa de PostgreSQL — usa SQLite)

```bash
cd backend
./venv/Scripts/python manage.py test --settings=core.settings_test
```

## Comandos administrativos

- `python manage.py seed_initial_data [--reset]` — cria o plano de contas
  padrão (receitas, despesas, não operacionais) e define a conta contábil
  padrão de aluguel nas configurações.
- `python manage.py import_properties --file <caminho.csv> [--dry-run]` —
  importa imóveis em lote. Use `docs/imoveis_template.csv` como modelo
  (Excel: salvar como CSV). `--dry-run` valida sem gravar.

## Módulos e endpoints principais

| Módulo | Endpoints |
|---|---|
| Imóveis (incl. terrenos) | `POST /properties/create/`, `GET/PATCH/DELETE /properties/<id>/`, `PATCH /properties/<id>/sold/` |
| Inquilinos | `POST /tenants/create/`, `GET/PATCH/DELETE /tenants/<id>/` |
| Contratos | `POST /contracts/create/` (gera cobranças automáticas), `GET/PATCH/DELETE /contracts/<id>/`, `POST /contracts/<id>/close/` |
| Emissão de arquivos | `GET /contracts/<id>/contract-pdf/` — contrato em PDF |
| Cobrança por e-mail | `GET /finance/collections/overdue/`, `GET /finance/collections/<id>/email-preview/`, `POST /finance/collections/<id>/send-email/`, `POST /finance/collections/mark-overdue/` |
| Financeiro | `/finance/transactions/` (+filtros `?account_type=&status=&year=&month=`), `/finance/bank_account/`, `/finance/chart_account/`, `/finance/entries/` |
| Analytics | `/analytics/summary`, `/analytics/dre/`, `/analytics/dfc/`, `/analytics/roe`, `/analytics/expiring`, `/analytics/default` |
| Configurações | `GET/PATCH /settings/` |

## E-mails de cobrança (SMTP)

Por padrão os e-mails são impressos no console do servidor (desenvolvimento).
Para envio real, defina no ambiente do backend:

```
EMAIL_HOST=smtp.seuprovedor.com
EMAIL_PORT=587
EMAIL_HOST_USER=voce@provedor.com
EMAIL_HOST_PASSWORD=senha-ou-senha-de-app
DEFAULT_FROM_EMAIL=voce@provedor.com
```

## Observações

- Alterar um contrato (valor/período) regera automaticamente as cobranças
  em aberto; o histórico pago/cancelado é preservado.
- Marcar uma cobrança como `PAID` (via PATCH em
  `/finance/transactions/<id>/`) cria automaticamente a entrada bancária e
  atualiza o saldo da conta.
- O vencimento dos aluguéis usa o dia definido no contrato; se o dia não
  existe no mês (ex.: dia 31 em fevereiro), cai no último dia do mês.
