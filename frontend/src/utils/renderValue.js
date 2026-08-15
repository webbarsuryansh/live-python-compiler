// Mirrors backend/app/execution/transform.py's _render_literal, but for display
// in the UI rather than regenerating source code.
export function renderValue(node, depth = 0) {
  if (!node) return "None";
  const { type, value } = node;

  switch (type) {
    case "NoneType":
      return "None";
    case "bool":
      return value ? "True" : "False";
    case "int":
    case "float":
      return String(value);
    case "str":
      return JSON.stringify(value);
    case "list":
      return `[${value.map((v) => renderValue(v, depth + 1)).join(", ")}]`;
    case "tuple":
      return `(${value.map((v) => renderValue(v, depth + 1)).join(", ")}${value.length === 1 ? "," : ""})`;
    case "set":
      return value.length ? `{${value.map((v) => renderValue(v, depth + 1)).join(", ")}}` : "set()";
    case "dict":
      return `{${value
        .map((e) => `${renderValue(e.key, depth + 1)}: ${renderValue(e.value, depth + 1)}`)
        .join(", ")}}`;
    case "function":
      return value;
    default:
      return String(value);
  }
}

export function shortTypeLabel(type) {
  if (type === "NoneType") return "none";
  return type;
}
