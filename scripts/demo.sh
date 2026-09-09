#!/usr/bin/env bash
set -e

BASE="http://localhost:8000"

section() {
    echo
    echo "=================================================================="
    echo "  $1"
    echo "=================================================================="
}

EMAIL="demo.$(date +%s)@demo.cl"

section "1. Crear empleado ($EMAIL)"
curl -s -w "\n  → HTTP %{http_code}\n" -X POST "$BASE/employees" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"Demo\",\"last_name\":\"Evaluación\",\"phone_number\":\"+56988887777\",\"email\":\"$EMAIL\"}"

EMPLOYEE_ID=$(curl -s "$BASE/employees?email=$EMAIL" | python3 -c "import json,sys; print(json.load(sys.stdin)['items'][0]['id'])")
echo "  empleado_id = $EMPLOYEE_ID"

section "2. Ver reglas laborales disponibles"
curl -s "$BASE/shift-rules" | python3 -c "
import json, sys
for r in json.load(sys.stdin)['items']:
    print(f\"  [{r['shift_rule_id']}] {r['name']}: {r['max_hours_day']}h/día, {r['max_hours_week']}h/semana\")"

section "3. Asignar regla 'Jornada Completa' (8h/día, 40h/semana)"
RULE_ID=$(curl -s "$BASE/shift-rules?name=Jornada" | python3 -c "import json,sys; print(json.load(sys.stdin)['items'][0]['shift_rule_id'])")
curl -s -w "\n  → HTTP %{http_code}\n" -X POST "$BASE/shift-rules-employees" \
    -H "Content-Type: application/json" \
    -d "{\"employee_id\":$EMPLOYEE_ID,\"shift_rule_id\":$RULE_ID}"

section "4. Crear turno VÁLIDO (lunes 08:00-12:00, 4h)"
curl -s -w "\n  → HTTP %{http_code}\n" -X POST "$BASE/shifts" \
    -H "Content-Type: application/json" \
    -d "{\"employee_id\":$EMPLOYEE_ID,\"shift_date\":\"2026-09-07\",\"start_time\":\"08:00\",\"end_time\":\"12:00\"}"

section "5. Crear turno INVÁLIDO (mismo día +5h → excede 8h diarias)"
curl -s -w "\n  → HTTP %{http_code}\n" -X POST "$BASE/shifts" \
    -H "Content-Type: application/json" \
    -d "{\"employee_id\":$EMPLOYEE_ID,\"shift_date\":\"2026-09-07\",\"start_time\":\"13:00\",\"end_time\":\"18:00\"}"

section "6. Crear turno NOCTURNO válido (martes 22:00 → miércoles 06:00, 8h)"
curl -s -w "\n  → HTTP %{http_code}\n" -X POST "$BASE/shifts" \
    -H "Content-Type: application/json" \
    -d "{\"employee_id\":$EMPLOYEE_ID,\"shift_date\":\"2026-09-08\",\"start_time\":\"22:00\",\"end_time\":\"06:00\"}"

section "7. Carga masiva con un ítem inválido → all-or-nothing (nada se inserta)"
curl -s -w "\n  → HTTP %{http_code}\n" -X POST "$BASE/shifts/bulk" \
    -H "Content-Type: application/json" \
    -d "[
      {\"employee_id\":$EMPLOYEE_ID,\"shift_date\":\"2026-09-09\",\"start_time\":\"08:00\",\"end_time\":\"16:00\"},
      {\"employee_id\":$EMPLOYEE_ID,\"shift_date\":\"2026-09-10\",\"start_time\":\"08:00\",\"end_time\":\"19:00\"}
    ]"

echo
echo "  verificando all-or-nothing (deben existir solo 2 turnos):"
curl -s "$BASE/shifts?employee_id=$EMPLOYEE_ID" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(f'  turnos del empleado: {d[\"total\"]} → {\"ALL-OR-NOTHING OK\" if d[\"total\"] == 2 else \"ERROR\"}')"

section "8. Carga masiva VÁLIDA (miércoles y jueves 8h)"
curl -s -w "\n  → HTTP %{http_code}\n" -X POST "$BASE/shifts/bulk" \
    -H "Content-Type: application/json" \
    -d "[
      {\"employee_id\":$EMPLOYEE_ID,\"shift_date\":\"2026-09-09\",\"start_time\":\"08:00\",\"end_time\":\"16:00\"},
      {\"employee_id\":$EMPLOYEE_ID,\"shift_date\":\"2026-09-10\",\"start_time\":\"08:00\",\"end_time\":\"16:00\"}
    ]"

section "9. Reporte del empleado (métricas día/semana)"
curl -s "$BASE/employees/$EMPLOYEE_ID/report?report_date=2026-09-09" | python3 -c "
import json, sys
d = json.load(sys.stdin)
m = d['metrics']
print(f\"  empleado: {d['employee']['name']} {d['employee']['last_name']}\")
print(f\"  regla: {d['shift_rule']['name']}\")
print(f\"  día {m['daily']['shift_date']}: {m['daily']['assigned_hours']}/{m['daily']['max_hours']}h ({m['daily']['usage_percent']}%)\")
print(f\"  semana {m['weekly']['week_start']} a {m['weekly']['week_end']}: {m['weekly']['assigned_hours']}/{m['weekly']['max_hours']}h ({m['weekly']['usage_percent']}%)\")
print(f\"  turnos programados: {d['shifts_total']}\")"

section "10. Intento de borrar empleado con turnos → 409"
curl -s -w "\n  → HTTP %{http_code}\n" -X DELETE "$BASE/employees/$EMPLOYEE_ID"

section "Demo completada — documenta y revísalo en http://localhost:8000/docs"
