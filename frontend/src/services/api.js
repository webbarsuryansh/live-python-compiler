const BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

export async function executeCode(code, { timeoutSeconds = 5, maxSteps = 2000 } = {}) {
  const res = await fetch(`${BASE_URL}/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      code,
      timeout_seconds: timeoutSeconds,
      max_steps: maxSteps,
    }),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Execution request failed (${res.status}): ${text}`);
  }

  return res.json();
}
