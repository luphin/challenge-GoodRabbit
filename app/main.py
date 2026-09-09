from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import (
    BulkValidationError,
    BusinessRuleError,
    ConflictError,
    NotFoundError,
    RuleViolationError,
)
from app.routers import employees, shift_rules, shift_rules_employees, shifts

TAGS_METADATA = [
    {
        "name": "Empleados",
        "description": "CRUD de empleados. Incluye el reporte consolidado por empleado.",
    },
    {
        "name": "Reglas laborales",
        "description": "CRUD de reglas: límites máximos de horas por día y por semana.",
    },
    {
        "name": "Asignación de reglas",
        "description": "Asigna una regla laboral activa a cada empleado (una por empleado).",
    },
    {
        "name": "Turnos",
        "description": (
            "CRUD de turnos con validación contra la regla laboral del empleado: "
            "límites diarios, semanales y traslapes. Incluye carga masiva."
        ),
    },
]

app = FastAPI(
    title=settings.app_name,
    description=(
        "API motor de asignación de turnos laborales. Cada turno se valida contra "
        "la regla laboral del empleado (límites de horas diarios y semanales); las "
        "operaciones inválidas se rechazan con código 422 y la causa en español."
    ),
    version=settings.app_version,
    docs_url="/docs",
    openapi_tags=TAGS_METADATA,
)


@app.exception_handler(NotFoundError)
def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ConflictError)
def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(BusinessRuleError)
def business_rule_handler(request: Request, exc: BusinessRuleError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(RuleViolationError)
def rule_violation_handler(request: Request, exc: RuleViolationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(BulkValidationError)
def bulk_validation_handler(request: Request, exc: BulkValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": [error.model_dump(mode="json") for error in exc.errors]},
    )


app.include_router(employees.router)
app.include_router(shift_rules.router)
app.include_router(shift_rules_employees.router)
app.include_router(shifts.router)


@app.get("/", summary="Raíz del servicio", tags=["Health"])
async def root():
    return {
        "service": "Challenge - API manejo de turnos.",
        "version": settings.app_version,
        "status": "active",
    }


@app.get("/health", summary="Health check del servicio", tags=["Health"])
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "environment": settings.environment,
        "version": settings.app_version,
    }
