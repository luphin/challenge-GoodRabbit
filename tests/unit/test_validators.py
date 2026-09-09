from datetime import date, datetime, time
from decimal import Decimal

import pytest

from app.core.exceptions import RuleViolationError
from app.services import validators


class TestShiftDurationHours:
    def test_horas_enteras(self):
        assert validators.shift_duration_hours(time(8, 0), time(12, 0)) == Decimal("4")

    def test_media_hora(self):
        assert validators.shift_duration_hours(time(8, 0), time(8, 30)) == Decimal("0.5")

    def test_quince_minutos(self):
        assert validators.shift_duration_hours(time(8, 0), time(8, 15)) == Decimal("0.25")

    def test_es_decimal_exacto_sin_redondeos(self):
        result = validators.shift_duration_hours(time(8, 0), time(8, 10))
        assert result == Decimal("1") / Decimal("6")
        assert isinstance(result, Decimal)

    def test_nocturno_22_a_06_son_8h(self):
        assert validators.shift_duration_hours(time(22, 0), time(6, 0)) == Decimal("8")

    def test_nocturno_23_a_0030_son_15h(self):
        assert validators.shift_duration_hours(time(23, 0), time(0, 30)) == Decimal("1.5")

    def test_nocturno_no_supera_24h(self):
        result = validators.shift_duration_hours(time(0, 1), time(0, 0))
        assert result == Decimal(86340) / Decimal(3600)
        assert result < Decimal("24")


class TestIsOvernight:
    def test_cruza_medianoche(self):
        assert validators.is_overnight(time(22, 0), time(6, 0)) is True

    def test_mismo_dia_no_es_nocturno(self):
        assert validators.is_overnight(time(8, 0), time(17, 0)) is False


class TestShiftBounds:
    def test_mismo_dia(self):
        start, end = validators.shift_bounds(date(2026, 9, 8), time(8, 0), time(12, 0))
        assert start == datetime(2026, 9, 8, 8, 0)
        assert end == datetime(2026, 9, 8, 12, 0)

    def test_nocturno_cruza_al_dia_siguiente(self):
        start, end = validators.shift_bounds(date(2026, 9, 8), time(22, 0), time(6, 0))
        assert start == datetime(2026, 9, 8, 22, 0)
        assert end == datetime(2026, 9, 9, 6, 0)


class TestWeekBounds:
    def test_miercoles_da_lunes_a_domingo(self):
        monday, sunday = validators.week_bounds(date(2026, 9, 9))
        assert monday == date(2026, 9, 7)
        assert sunday == date(2026, 9, 13)

    def test_lunes_incluye_toda_la_semana(self):
        monday, sunday = validators.week_bounds(date(2026, 9, 7))
        assert monday == date(2026, 9, 7)
        assert sunday == date(2026, 9, 13)

    def test_domingo_cierra_la_semana(self):
        monday, sunday = validators.week_bounds(date(2026, 9, 13))
        assert monday == date(2026, 9, 7)
        assert sunday == date(2026, 9, 13)

    def test_cambio_de_semana(self):
        monday, _ = validators.week_bounds(date(2026, 9, 13))
        next_monday, _ = validators.week_bounds(date(2026, 9, 14))
        assert next_monday > monday


class TestValidateTimes:
    def test_horario_valido_pasa(self):
        validators.validate_times(time(8, 0), time(17, 0))

    def test_nocturno_valido_pasa(self):
        validators.validate_times(time(22, 0), time(6, 0))

    def test_duracion_cero_rechaza(self):
        with pytest.raises(RuleViolationError, match="mayor a cero"):
            validators.validate_times(time(10, 0), time(10, 0))


class TestValidateDailyLimit:
    def test_en_el_limite_exacto_pasa(self):
        validators.validate_daily_limit(
            employee_id=1,
            shift_date=date(2026, 9, 8),
            existing_hours=Decimal("4"),
            shift_hours=Decimal("4"),
            max_hours_day=Decimal("8"),
        )

    def test_excedente_minimo_rechaza(self):
        with pytest.raises(RuleViolationError, match="excede el límite diario"):
            validators.validate_daily_limit(
                employee_id=1,
                shift_date=date(2026, 9, 8),
                existing_hours=Decimal("7.5"),
                shift_hours=Decimal("0.75"),
                max_hours_day=Decimal("8"),
            )

    def test_mensaje_incluye_excedente(self):
        with pytest.raises(RuleViolationError, match=r"excedente: 0\.25h"):
            validators.validate_daily_limit(
                employee_id=1,
                shift_date=date(2026, 9, 8),
                existing_hours=Decimal("7.75"),
                shift_hours=Decimal("0.5"),
                max_hours_day=Decimal("8"),
            )


class TestValidateWeeklyLimit:
    def test_en_el_limite_exacto_pasa(self):
        validators.validate_weekly_limit(
            employee_id=1,
            week_start=date(2026, 9, 7),
            week_end=date(2026, 9, 13),
            existing_hours=Decimal("38"),
            shift_hours=Decimal("2"),
            max_hours_week=Decimal("40"),
        )

    def test_excedente_rechaza(self):
        with pytest.raises(RuleViolationError, match="límite semanal"):
            validators.validate_weekly_limit(
                employee_id=1,
                week_start=date(2026, 9, 7),
                week_end=date(2026, 9, 13),
                existing_hours=Decimal("40"),
                shift_hours=Decimal("0.5"),
                max_hours_week=Decimal("40"),
            )


class TestValidateNoOverlap:
    def test_sin_traslape_pasa(self):
        validators.validate_no_overlap(
            employee_id=1,
            new_start=datetime(2026, 9, 8, 14, 0),
            new_end=datetime(2026, 9, 8, 18, 0),
            overlapping=None,
        )

    def test_traslape_rechaza(self):
        with pytest.raises(RuleViolationError, match="traslapa"):
            validators.validate_no_overlap(
                employee_id=1,
                new_start=datetime(2026, 9, 8, 11, 0),
                new_end=datetime(2026, 9, 8, 13, 0),
                overlapping=(datetime(2026, 9, 8, 8, 0), datetime(2026, 9, 8, 12, 0)),
            )

    def test_adyacente_no_es_traslape(self):
        validators.validate_no_overlap(
            employee_id=1,
            new_start=datetime(2026, 9, 8, 12, 0),
            new_end=datetime(2026, 9, 8, 16, 0),
            overlapping=(datetime(2026, 9, 8, 8, 0), datetime(2026, 9, 8, 12, 0)),
        )

    def test_nocturno_traslape_cruzando_medianoche(self):
        with pytest.raises(RuleViolationError, match="traslapa"):
            validators.validate_no_overlap(
                employee_id=1,
                new_start=datetime(2026, 9, 9, 5, 0),
                new_end=datetime(2026, 9, 9, 9, 0),
                overlapping=(datetime(2026, 9, 8, 22, 0), datetime(2026, 9, 9, 6, 0)),
            )

    def test_nocturno_adyacente_despues_pasa(self):
        validators.validate_no_overlap(
            employee_id=1,
            new_start=datetime(2026, 9, 9, 6, 0),
            new_end=datetime(2026, 9, 9, 10, 0),
            overlapping=(datetime(2026, 9, 8, 22, 0), datetime(2026, 9, 9, 6, 0)),
        )


class TestFormatHours:
    def test_entero_sin_decimales_inutiles(self):
        assert validators._format_hours(Decimal("40.00")) == "40"

    def test_decimal_con_parte_fraccional(self):
        assert validators._format_hours(Decimal("7.50")) == "7.5"

    def test_notacion_cientifica_evitada(self):
        assert validators._format_hours(Decimal("40.00").normalize()) == "40"
