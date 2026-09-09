class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass


class BusinessRuleError(Exception):
    pass


class RuleViolationError(Exception):
    pass


class BulkValidationError(Exception):
    def __init__(self, errors: list) -> None:
        self.errors = errors
        super().__init__(
            f"{len(errors)} turno(s) del lote no cumplen las reglas de negocio"
        )
