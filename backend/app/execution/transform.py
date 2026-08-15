"""Builds the "Runtime" view of the source: the same program, but every line
that assigns or mutates a variable is collapsed down to a single line showing
that variable's value *at the target step*, in whatever line position was the
last one to touch it up to that point. The original source is never modified
— this only ever produces a second, derived string.

Generic by design: it walks the AST looking for (a) plain assignments to a
Name, (b) augmented assignments to a Name, (c) subscript assignments to a
Name (`x[i] = ...`), and (d) attribute-call statements on a Name
(`x.append(...)`, `x.update(...)`, etc.) — it does not special-case any
specific method.
"""
from __future__ import annotations

import ast


def _render_literal(node: dict, indent: int = 0) -> str:
    """Render a serialize.to_safe() node back into a Python-literal-ish string."""
    t = node.get("type")
    v = node.get("value")

    if t == "NoneType":
        return "None"
    if t in ("int", "float", "bool"):
        return repr(v)
    if t == "str":
        return repr(v)
    if t == "list":
        inner = ", ".join(_render_literal(x, indent) for x in v)
        return f"[{inner}]"
    if t == "tuple":
        inner = ", ".join(_render_literal(x, indent) for x in v)
        return f"({inner}{',' if len(v) == 1 else ''})"
    if t == "set":
        if not v:
            return "set()"
        inner = ", ".join(_render_literal(x, indent) for x in v)
        return f"{{{inner}}}"
    if t == "dict":
        inner = ", ".join(
            f"{_render_literal(e['key'], indent)}: {_render_literal(e['value'], indent)}"
            for e in v
        )
        return f"{{{inner}}}"
    # Fallback: functions, custom objects, truncated values, etc.
    return str(v)


def _target_names(node: ast.stmt):
    """Return the list of simple variable names this top-level statement
    assigns to or mutates, or [] if it isn't a variable-touching statement
    we know how to collapse.
    """
    if isinstance(node, ast.Assign):
        names = []
        for target in node.targets:
            if isinstance(target, ast.Name):
                names.append(target.id)
            elif isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name):
                names.append(target.value.id)
        return names

    if isinstance(node, ast.AugAssign):
        if isinstance(node.target, ast.Name):
            return [node.target.id]
        if isinstance(node.target, ast.Subscript) and isinstance(node.target.value, ast.Name):
            return [node.target.value.id]
        return []

    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
        func = node.value.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            return [func.value.id]

    return []


def build_runtime_source(original_source: str, variables: dict) -> str:
    """Return the collapsed runtime-view source for the given final `variables`
    snapshot (as produced by serialize.snapshot_vars).
    """
    try:
        tree = ast.parse(original_source)
    except SyntaxError:
        # Can't safely transform invalid syntax — just echo it back.
        return original_source

    lines = original_source.splitlines()
    touched_lines_by_var: dict[str, list[int]] = {}

    for node in tree.body:
        if not hasattr(node, "lineno"):
            continue
        names = _target_names(node)
        end_line = getattr(node, "end_lineno", node.lineno)
        for name in names:
            touched_lines_by_var.setdefault(name, []).append(node.lineno)
        # Track the full span so we can blank out multi-line statements too.
        node._span = (node.lineno, end_line)  # type: ignore[attr-defined]

    anchor_line_for_var = {name: max(nums) for name, nums in touched_lines_by_var.items()}
    anchor_lines = set(anchor_line_for_var.values())
    all_touched_lines = {ln for nums in touched_lines_by_var.values() for ln in nums}

    # Map: lineno -> variable name it should render as the anchor for.
    var_by_anchor_line = {ln: name for name, ln in anchor_line_for_var.items()}

    output = []
    for node in tree.body:
        if not hasattr(node, "lineno"):
            continue
        start, end = getattr(node, "_span", (node.lineno, node.lineno))
        names = _target_names(node)

        if not names:
            # Untouched statement (e.g. print(x), a for-loop, a function def) —
            # keep verbatim.
            output.extend(lines[start - 1:end])
            continue

        if start in anchor_lines and var_by_anchor_line.get(start) in names:
            name = var_by_anchor_line[start]
            indent = lines[start - 1][: len(lines[start - 1]) - len(lines[start - 1].lstrip())]
            if name in variables:
                rendered = _render_literal(variables[name])
                output.append(f"{indent}{name} = {rendered}")
            else:
                output.extend(lines[start - 1:end])
        else:
            # A non-final touch on this variable — collapsed away since the
            # anchor line already reflects the end state.
            continue

    return "\n".join(output) if output else original_source
