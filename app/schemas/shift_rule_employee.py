from pydantic import BaseModel, ConfigDict


class ShiftRuleEmployeeCreate(BaseModel):
    employee_id: int
    shift_rule_id: int


class ShiftRuleEmployeeUpdate(BaseModel):
    shift_rule_id: int


class ShiftRuleEmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    shift_rule_r_employee_id: int
    employee_id: int
    shift_rule_id: int
