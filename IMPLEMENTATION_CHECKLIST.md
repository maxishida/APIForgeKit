# APIForgeKit Studio V1 Implementation Checklist

## O que foi implementado

- NiceGUI local app em `app.py`.
- Shell visual com sidebar, header, cards e tema Dark/Neon Blue.
- Lead Algorithm Lab determinístico.
- Dashboard com métricas e gráficos Plotly.
- PostgreSQL Docker com SQLAlchemy.
- Logs JSONL em `logs/lead_tests.jsonl`.
- Tela Logs com filtros, busca, AG Grid, JSON completo e export CSV/JSONL.
- Context Builder com export Markdown.
- Next.js Blueprint Generator com Prisma local como orientação.
- Testes unitários com Pytest.
- Lab antigo de providers preservado como legado.

## Como rodar

```bash
python -m pip install -r requirements.txt
copy .env.example .env
docker compose up -d
python app.py
```

Abra `http://localhost:8080`.

## Bibliotecas usadas

- `nicegui`
- `plotly`
- `pandas`
- `sqlalchemy`
- `psycopg[binary]`
- `python-dotenv`
- `pydantic-settings`
- `loguru`
- `pytest`

## Como testar algoritmo

```bash
python -m pytest tests/test_lead_algorithm.py -q
```

## Como ver dashboard

1. Suba o banco com `docker compose up -d`.
2. Rode `python app.py`.
3. Acesse `http://localhost:8080`.
4. Abra a página Dashboard.

## Como ler logs

- Pela UI: página Logs.
- No arquivo local: `logs/lead_tests.jsonl`.
- No banco: tabela `lead_tests`.

## Como gerar contexto

1. Execute testes no Lead Algorithm Lab.
2. Abra Context Builder.
3. Clique em Exportar Markdown.
4. Veja o arquivo em `exports/contexts/`.

## Como gerar blueprint Next.js

1. Abra Next.js Blueprint.
2. Clique em Exportar Blueprint.
3. Veja o arquivo em `exports/blueprints/`.

## Próximos passos V2

- Autenticação local opcional.
- Migrations formais com Alembic.
- Templates completos de código Next.js.
- Integração com Prisma em projeto Next real.
- Observabilidade avançada com filtros por período e live refresh completo.
- Testes end-to-end de UI.

## Bugs conhecidos

- A UI depende do PostgreSQL para executar testes reais; sem banco, abre em modo degradado.
- Export CSV/JSONL grava arquivo local e mostra o caminho, sem download automático pelo navegador.

## Pendências

- Criar suite visual automatizada para screenshots.
- Adicionar paginação server-side para volumes muito altos.
- Adicionar migrações versionadas antes de uso fora do MVP local.
