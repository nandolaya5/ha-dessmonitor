"""Pure helpers for deriving number-entity slider range and step.

Kept free of Home Assistant imports so the logic can be unit-tested in
isolation. See ``number.py`` for the entity that consumes it.
"""

from __future__ import annotations

import re

# Units whose controls are adjusted in fine increments and whose values are
# never negative (voltages, currents).
_VOLT_AMP = ("V", "A")

# When the API hint is missing or inconsistent with the live value, synthesize a
# slider range around the known-good live value. The range is deliberately
# generous: the DessMonitor/SmartESS API rejects genuinely out-of-range writes,
# so a too-narrow range (which blocks valid setpoints) is worse than a wide one.
_RANGE_HEADROOM = 0.5
_MIN_RANGE_SPAN = {"V": 5.0, "A": 5.0}
# Fallback max for a V/A control that has neither a usable hint nor a live value.
_UNIT_FALLBACK_MAX = {"V": 100.0, "A": 100.0}


def parse_hint_range(hint: str) -> tuple[float | None, float | None]:
    """Parse min/max from a hint string like '60.0~66V' or '0-900min'."""
    numbers = re.findall(r"[\d.]+", hint)
    if len(numbers) >= 2:
        try:
            a, b = float(numbers[0]), float(numbers[1])
            return (min(a, b), max(a, b))
        except ValueError:
            pass
    return None, None


def compute_range_and_step(
    unit: str | None, hint: str | None, value: float | None
) -> tuple[float | None, float | None, float]:
    """Compute ``(min, max, step)`` for a value control.

    Step is derived from the unit (``0.1`` for V/A, else ``1.0``) and is always
    returned, otherwise hint-less voltage/current fields fall back to Home
    Assistant's coarse default step of ``1`` (issue #23).

    For the range we trust the API hint only when it is present and actually
    brackets the device's current value. The DessMonitor/SmartESS API has been
    observed returning hints that are wrong or missing for charging-voltage and
    current controls (e.g. a ``25-30V`` hint on a 48V system whose live setting
    is ``57.6V`` (issue #22), or no hint at all so HA defaults to ``0-100``
    (issue #23)). In those cases the slider is unusable and writes of otherwise
    valid values are rejected as "out of range". We therefore synthesize a
    generous range around the live value; the API still rejects genuinely
    invalid writes, so erring wide is safe while erring narrow blocks valid
    setpoints.

    A returned ``min`` or ``max`` of ``None`` means "leave HA's default".
    """
    unit = (unit or "").strip()
    step = 0.1 if unit in _VOLT_AMP else 1.0

    lo, hi = parse_hint_range(hint) if hint else (None, None)

    # 1. A complete hint that brackets the live value (or when there is no value
    #    to contradict it) is trusted as-is.
    if lo is not None and hi is not None and (value is None or lo <= value <= hi):
        return lo, hi, step

    # 2. The hint is missing or doesn't cover the live value.
    if value is not None:
        if unit in _VOLT_AMP:
            # Anchor a generous range on the known-good live value.
            span = max(abs(value) * _RANGE_HEADROOM, _MIN_RANGE_SPAN[unit])
            cand_lo = max(0.0, value - span)
            cand_hi = value + span
            new_lo = cand_lo if lo is None else min(lo, cand_lo)
            new_hi = cand_hi if hi is None else max(hi, cand_hi)
            return round(new_lo, 1), round(new_hi, 1), step
        # For other units we can't guess a sensible magnitude, so only widen an
        # existing hint outward to include the value rather than invent a range.
        if lo is not None and value < lo:
            lo = value
        if hi is not None and value > hi:
            hi = value
        return lo, hi, step

    # 3. No live value to anchor on. Give V/A a usable default range; for other
    #    units leave HA's defaults alone.
    if unit in _VOLT_AMP:
        return (
            lo if lo is not None else 0.0,
            hi if hi is not None else _UNIT_FALLBACK_MAX[unit],
            step,
        )
    return lo, hi, step
