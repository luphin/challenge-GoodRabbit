# API de Gestión de Turnos Laborales

API REST en Python (FastAPI) que funciona como motor de asignación de turnos,
actuando como **filtro inteligente**: cada turno se valida contra la regla
laboral del empleado (límites diarios y semanales) antes de persistirse; toda
operación inválida se rechaza con código 422 y la causa en español.

El dominio completo - lenguaje ubicuo, reglas de negocio (BR-01…BR-10), modelo
ER, arquitectura y requisitos está en
[`docs/MODELO_DE_NEGOCIO.md`](docs/MODELO_DE_NEGOCIO.md).

## Despliegue

> Definir `.env`, solo para pruebas `cat .env.example > .env`

### **Recomendado: contenedor.** Migración automática del esquema al arrancar:

```bash
docker compose up --build
docker compose exec api python scripts/seed.py   # datos demo (idempotente, opcional)
```

| Servicio | URL |
|---|---|
| API | http://localhost:8000 |
| Swagger (`/docs`) | http://localhost:8000/docs |
| Adminer | http://localhost:8080  \ sytem: `PostgreSQL`, servidor: `db`, usuario: `turnos`, clave: `turnos_dev` |

## Demo del flujo completo del enunciado (reset de BD incluido):

```bash
make demo
```

### Alternativa: desarrollo local (referencia)

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env                              # ajustar credenciales

docker compose up -d db                           # solo PostgreSQL
.venv/bin/alembic upgrade head                    # crear esquema
.venv/bin/python scripts/seed.py                  # datos demo
.venv/bin/uvicorn app.main:app --reload --port 8000
```

## Testing

```bash
make test                                          # pytest + cobertura: 104 tests, 99% en app/services
.venv/bin/pytest tests/unit                        # validadores puros, sin BD (milisegundos)
.venv/bin/pytest tests/integration                 # API completa contra BD de test
.venv/bin/pytest -k "traslape"                     # filtrar por nombre
.venv/bin/pytest -x                                # detener en el primer fallo
```

La suite usa una BD dedicada (`turnos_test`, creada automáticamente en
volúmenes nuevos por `db/init/`) con **patrón transaccional**: cada test corre
dentro de una transacción que se revierte, sin truncate entre tests.

## QA - lint, tipos y formato

```bash
make qa          # flujo completo: lint + types + test
make lint        # ruff check (0 violaciones)
make types       # mypy (0 errores en 33 archivos)

.venv/bin/ruff format app tests scripts    # auto-formateo (opcional, fuera del qa)
```

## Estructura

```
app/
├── main.py           # app, routers, handlers de excepciones
├── core/             # config (.env), excepciones de dominio
├── db/               # engine, session (get_db), base declarativa
├── models/           # Employee, Shift, ShiftRule, ShiftRuleEmployee
├── schemas/          # Pydantic: Create/Read/Update/Bulk/Report/Page
├── routers/          # HTTP puro
├── services/         # negocio, validadores, reportes
alembic/              # migraciones versionadas (se evolucionan con Alembic)
scripts/seed.py       # datos demo idempotentes
scripts/demo.sh       # demo end-to-end del flujo del enunciado
tests/                # unit/ (validadores) + integration/ (API)
docs/                 # modelo de negocio, guía de desarrollo, comandos
```

## Estado y pendientes

-  CHECK  - CRUD completo, validaciones, bulk all-or-nothing, reportes
-  CHECK  - Soft delete de empleados (desactivar/reactivar, BR-09/BR-11)
-  CHECK  - 104 tests (99% cobertura), ruff y mypy limpios, demo end-to-end (scripts/demo.sh)
-  MEJORA - CI (GitHub Actions) y Dockerfile multi-stage de producción

## Documentación

| Documento | Contenido |
|---|---|
| [`docs/MODELO_DE_NEGOCIO.md`](docs/MODELO_DE_NEGOCIO.md) | Lenguaje ubicuo, reglas de negocio, modelo ER, arquitectura, requisitos y tecnologías |
| [`docs/COMMANDS.md`](docs/COMMANDS.md) | Comandos de operación: Docker, Alembic, testing, demo |
