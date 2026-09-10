from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ShiftRuleCreate(BaseModel):
    name: str = Field(min_length=1)
    max_hours_day: Decimal = Field(gt=0, le=24)
    max_hours_week: Decimal = Field(gt=0, le=168)

    @model_validator(mode="after")
    def week_not_less_than_day(self) -> "ShiftRuleCreate":
        if self.max_hours_week < self.max_hours_day:
            raise ValueError("max_hours_week no puede ser menor que max_hours_day")
        return self


class ShiftRuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    max_hours_day: Decimal | None = Field(default=None, gt=0, le=24)
    max_hours_week: Decimal | None = Field(default=None, gt=0, le=168)

    @model_validator(mode="after")
    def week_not_less_than_day(self) -> "ShiftRuleUpdate":
        day = self.max_hours_day
        week = self.max_hours_week
        if day is not None and week is not None and week < day:
            raise ValueError("max_hours_week no puede ser menor que max_hours_day")
        return self


class ShiftRuleRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": [
                {
                    "shift_rule_id": 1,
                    "name": "Jornada Completa",
                    "max_hours_day": "8.00 or 8",
                    "max_hours_week": "40.00 or 40",
                }
            ]
        },
    )

    shift_rule_id: int
    name: str
    max_hours_day: Decimal
    max_hours_week: Decimal
