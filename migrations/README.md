# Migrations

APIForgeKit still boots with `Base.metadata.create_all()` for local-first DX, but Alembic is available for users who want versioned PostgreSQL changes.

Run:

```bash
npm run db:migrate
```
