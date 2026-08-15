"""Convert arbitrary runtime Python values into JSON-safe, type-tagged structures
so the frontend can render lists/dicts/sets/objects generically without the
backend having to special-case any particular container operation.
"""
from __future__ import annotations

MAX_DEPTH = 6
MAX_ITEMS = 500
MAX_STR_LEN = 4000


def type_name(value) -> str:
    return type(value).__name__


def to_safe(value, depth: int = 0, _seen: set | None = None):
    """Recursively convert `value` into a JSON-safe representation.

    Every node is returned as {"type": <pyTypeName>, "value": <jsonSafeValue>}
    so the frontend can branch on `type` to decide how to render/animate it,
    without any operation-specific (append/pop/etc.) knowledge baked in here.
    """
    if _seen is None:
        _seen = set()

    if depth > MAX_DEPTH:
        return {"type": "truncated", "value": "…"}

    t = type(value)

    if value is None:
        return {"type": "NoneType", "value": None}
    if t is bool:
        return {"type": "bool", "value": value}
    if t is int:
        return {"type": "int", "value": value}
    if t is float:
        return {"type": "float", "value": value}
    if t is str:
        v = value if len(value) <= MAX_STR_LEN else value[:MAX_STR_LEN] + "…"
        return {"type": "str", "value": v}

    obj_id = id(value)
    if obj_id in _seen and t in (list, dict, set, tuple):
        return {"type": type_name(value), "value": "…circular…"}

    if t is list:
        _seen = _seen | {obj_id}
        items = [to_safe(v, depth + 1, _seen) for v in value[:MAX_ITEMS]]
        return {"type": "list", "value": items, "truncated": len(value) > MAX_ITEMS}

    if t is tuple:
        _seen = _seen | {obj_id}
        items = [to_safe(v, depth + 1, _seen) for v in value[:MAX_ITEMS]]
        return {"type": "tuple", "value": items, "truncated": len(value) > MAX_ITEMS}

    if t is set or t is frozenset:
        _seen = _seen | {obj_id}
        try:
            ordered = sorted(value, key=lambda x: repr(x))
        except Exception:
            ordered = list(value)
        items = [to_safe(v, depth + 1, _seen) for v in ordered[:MAX_ITEMS]]
        return {"type": "set", "value": items, "truncated": len(value) > MAX_ITEMS}

    if t is dict:
        _seen = _seen | {obj_id}
        entries = []
        for i, (k, v) in enumerate(value.items()):
            if i >= MAX_ITEMS:
                break
            entries.append({
                "key": to_safe(k, depth + 1, _seen),
                "value": to_safe(v, depth + 1, _seen),
            })
        return {"type": "dict", "value": entries, "truncated": len(value) > MAX_ITEMS}

    if callable(value):
        name = getattr(value, "__name__", repr(value))
        return {"type": "function", "value": f"<function {name}>"}

    # Fallback: any other object (custom class instances, modules, etc.)
    try:
        r = repr(value)
    except Exception:
        r = f"<{type_name(value)} object>"
    if len(r) > MAX_STR_LEN:
        r = r[:MAX_STR_LEN] + "…"
    return {"type": type_name(value), "value": r}


def snapshot_vars(mapping: dict) -> dict:
    """Serialize a variable name -> value mapping, skipping dunders/builtins."""
    out = {}
    for k, v in mapping.items():
        if k.startswith("__") and k.endswith("__"):
            continue
        out[k] = to_safe(v)
    return out
