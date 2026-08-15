"""Compute a generic diff between two already-serialized variable snapshots.

This is intentionally operation-agnostic: it never knows about `.append`,
`.pop`, etc. It only compares the *resulting* JSON-safe values from one step
to the next and reports what changed, which is enough for the frontend to
animate additions/removals/updates for any container type.
"""


def _index_diff(prev_items: list, curr_items: list):
    """Best-effort positional diff for list/tuple/set-like sequences.
    Returns (added_indices, removed_indices) relative to curr/prev respectively.
    Good enough for common single-mutation cases (append/pop/insert/remove/[i]=).
    """
    prev_reprs = [repr(i) for i in prev_items]
    curr_reprs = [repr(i) for i in curr_items]

    added_indices = []
    removed_indices = []

    if len(curr_reprs) > len(prev_reprs) and curr_reprs[: len(prev_reprs)] == prev_reprs:
        added_indices = list(range(len(prev_reprs), len(curr_reprs)))
    elif len(curr_reprs) < len(prev_reprs) and prev_reprs[: len(curr_reprs)] == curr_reprs:
        removed_indices = list(range(len(curr_reprs), len(prev_reprs)))
    else:
        # Fall back to a simple pairwise compare for in-place edits (e.g. lst[i] = x)
        for i in range(min(len(prev_reprs), len(curr_reprs))):
            if prev_reprs[i] != curr_reprs[i]:
                added_indices.append(i)

    return added_indices, removed_indices


def diff_variables(prev_snapshot: dict, curr_snapshot: dict) -> dict:
    changes = {}
    keys = set(prev_snapshot.keys()) | set(curr_snapshot.keys())

    for key in keys:
        prev = prev_snapshot.get(key)
        curr = curr_snapshot.get(key)

        if prev is None and curr is not None:
            changes[key] = {"kind": "added", "previous": None, "current": curr}
            continue
        if prev is not None and curr is None:
            changes[key] = {"kind": "removed", "previous": prev, "current": None}
            continue
        if prev == curr:
            changes[key] = {"kind": "unchanged", "previous": prev, "current": curr}
            continue

        entry = {"kind": "modified", "previous": prev, "current": curr}

        if curr.get("type") in ("list", "tuple", "set") and prev.get("type") == curr.get("type"):
            added, removed = _index_diff(prev.get("value", []), curr.get("value", []))
            entry["added_indices"] = added
            entry["removed_indices"] = removed

        changes[key] = entry

    return changes
