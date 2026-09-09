# Comandos del proyecto — API de Turnos Laborales

> Referencia rápida de los comandos utiles, organizados por fase.
> Todos los comandos se corren desde la raíz del proyecto.

---

## Entorno y aplicación

### Entorno virtual

```bash
# Verificar versiones instaladas (Python ≥ 3.12)
python3 --version
docker --version

# Crear el entorno virtual (carpeta .venv con su propio site-packages)
python3 -m venv .venv

# Activarlo (zsh/macOS) — hay que activarlo en cada terminal nueva
. .venv/bin/activate

# Desactivarlo cuando se termine la sesión
deactivate
```

### Dependencias

```bash
# Instalar todo
pip install -r requirements.txt

# Estas son para ocupar el ruff y mypy (linting y formato)
pip install -r requirements-dev.txt 
```

### Ejecutar la API

```bash
# Servidor de desarrollo con hot-reload (detecta cambios y reinicia solo)
uvicorn app.main:app --reload --port 8000

# Probar el health check y la documentación
curl localhost:8000/health
# Abrir en el navegador:
#   http://localhost:8000/docs        (Swagger UI)
#   http://localhost:8000/redoc       (alternativa de docs)
```

---

## Docker

```bash
# Levantar TODOS los servicios (db + api + adminer). --build reconstruye la
# imagen de la API: obligatorio cuando cambia requirements.txt o el Dockerfile
docker compose up --build

# Levantar solo la BD en segundo plano (modo -d = detached)
docker compose up -d db

# Esperar a que Postgres acepte conexiones (loop hasta que el healthcheck pase)
until docker compose exec db pg_isready -U turnos -d turnos > /dev/null 2>&1; do sleep 2; done

# Ver el estado de los contenedores y sus health checks
docker compose ps

# Ver los logs de un servicio en vivo
docker compose logs -f api

# Apagar todos los contenedores (los DATOS del volumen pgdata SOBREVIVEN)
docker compose down

# Apagar Y BORRAR el volumen de datos (reset total de la BD — "formatear")
docker compose down -v

# Reconstruir solo la imagen de la API sin levantar nada
docker compose build api

# Debugger de compose (sin la flag muestra hasta los secrets)
docker compose config --quiet
```

---

## Persistencia (Alembic + seed)

### Alembic

```bash
# Generar la estructura oficial de Alembic (alembic.ini + alembic/env.py + versions/)
alembic init alembic

# Crear una migración autogenerada: compara los modelos Python contra la BD real
# y escribe el diff. 
alembic revision --autogenerate -m "tablas iniciales: employees, shift_rules, shifts, shift_rules_employees"

# Aplicar todas las migraciones pendientes hasta la última (head)
alembic upgrade head

# Deshacer la última migración aplicada
alembic downgrade -1

# Ver el estado actual: qué migración está aplicada y cuáles existen
alembic current
alembic history
```

### Verificación en la base de datos

```bash
# Entrar a psql dentro del contenedor de Postgres
docker compose exec db psql -U turnos -d turnos

# (dentro de psql)
#   \dt          → listar tablas
#   \d shifts    → describir la tabla shifts (columnas, FKs, índices)
#   \q           → salir

# Listar tablas sin entrar al shell interactivo
docker compose exec db psql -U turnos -d turnos -c "\dt"

# Ver los datos sembrados: empleado + su regla laboral (JOIN)
docker compose exec db psql -U turnos -d turnos -c "
SELECT e.email, r.name AS regla, r.max_hours_day, r.max_hours_week
FROM employees e
JOIN shift_rules_employees sre ON sre.employee_id = e.id
JOIN shift_rules r ON r.shift_rule_id = sre.shift_rule_id
ORDER BY e.id;"
```

### Seed

```bash
# Cargar datos demo. Es IDEMPOTENTE: se puede correr N veces sin duplicar
python scripts/seed.py
```

---

## Fase 6 — Testing

```bash
# Correr TODA la suite (97 tests: unitarios + integración)
pytest

# Con reporte de cobertura (objetivo: ≥85% en app/services)
pytest --cov

# Cobertura solo de la capa de dominio, con líneas faltantes
pytest --cov --cov-report=term-missing

# Correr solo los unitarios de validadores (sin BD, milisegundos)
pytest tests/unit

# Correr solo los de integración
pytest tests/integration

# Correr un archivo o un test específico (útil al depurar)
pytest tests/integration/test_shifts.py
pytest tests/integration/test_shifts.py::test_limite_diario_exacto_201

# Correr los tests cuyo nombre coincida con un patrón
pytest -k "traslape"

# Modo verbose: muestra cada test individual
pytest -v

# Detener en el primer fallo
pytest -x
```

### Base de datos de test

```bash
# Crear la BD de test (misma instancia, distinta base) — solo la primera vez
echo "SELECT 'CREATE DATABASE turnos_test' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'turnos_test')\gexec" | docker compose exec -T db psql -U turnos -d postgres

# Los tests NO tocan la BD de desarrollo: conftest.py apunta DATABASE_URL a
# turnos_test y cada test corre dentro de una transacción que se revierte.
```

---

## Makefile — flujo de calidad

```bash
make lint    # ruff check sobre app/, tests/ y scripts/
make types   # mypy sobre app/ (0 errores esperados)
make test    # pytest con cobertura
make qa      # lint + types + test (todo el flujo de QA)

make demo    # ensayo general completo: reset de volúmenes, rebuild, espera de
             # health, seed manual y ejecución de scripts/demo.sh
```

## Demo end-to-end

```bash
# La migración corre AUTOMÁTICA al arrancar el contenedor api;
# el seed es MANUAL (datos demo son decisión del operador):
docker compose up --build -d
docker compose exec api python scripts/seed.py
bash scripts/demo.sh

# demo.sh ejecuta el flujo completo del enunciado:
# empleado → regla → turno válido → turno inválido (422 con causa) →
# turno nocturno → bulk all-or-nothing → bulk válido → reporte → delete 409
```

### Base de datos de test

```bash
# La BD de test se crea AUTOMÁTICAMENTE en volúmenes nuevos mediante
# db/init/01-create-test-db.sql (montado en /docker-entrypoint-initdb.d).
# Solo si el volumen ya existía sin turnos_test, créala a mano:
echo "SELECT 'CREATE DATABASE turnos_test' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'turnos_test')\gexec" | docker compose exec -T db psql -U turnos -d postgres

# Los tests NO tocan la BD de desarrollo: conftest.py apunta DATABASE_URL a
# turnos_test y cada test corre dentro de una transacción que se revierte.
```

---

## Orden de arranque completo de arranque sin el contenedor Docker (para desarrollo local)

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
docker compose up -d db
until docker compose exec db pg_isready -U turnos -d turnos > /dev/null 2>&1; do sleep 2; done
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload --port 8000
```
