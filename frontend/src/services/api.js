const BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

// Token management
let accessToken = localStorage.getItem("lpc_token") || "";
let refreshToken = localStorage.getItem("lpc_refresh_token") || "";

export function setTokens(newAccessToken, newRefreshToken) {
  accessToken = newAccessToken;
  refreshToken = newRefreshToken;
  if (newAccessToken) {
    localStorage.setItem("lpc_token", newAccessToken);
  } else {
    localStorage.removeItem("lpc_token");
  }
  if (newRefreshToken) {
    localStorage.setItem("lpc_refresh_token", newRefreshToken);
  } else {
    localStorage.removeItem("lpc_refresh_token");
  }
}

export function getAccessToken() {
  return accessToken;
}

export function clearTokens() {
  setTokens("", "");
}

async function request(path, options = {}, token = null) {
  const headers = { ...(options.headers || {}) };
  if (options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  // If token expired, try to refresh
  if (res.status === 401 && refreshToken && token === accessToken) {
    try {
      const refreshRes = await fetch(`${BASE_URL}/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      
      if (refreshRes.ok) {
        const data = await refreshRes.json();
        setTokens(data.token, data.refresh_token);
        
        // Retry request with new token
        headers.Authorization = `Bearer ${data.token}`;
        res = await fetch(`${BASE_URL}${path}`, {
          ...options,
          headers,
        });
      }
    } catch (err) {
      // Refresh failed, continue with original error
      clearTokens();
    }
  }

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    let message = text;
    try {
      const body = JSON.parse(text);
      message = body.detail || body.message || text;
    } catch {
      // Keep the raw response when the server did not return JSON.
    }
    throw new Error(message || `Request failed (${res.status})`);
  }

  if (res.status === 204) return null;
  return res.json();
}

// ===== Authentication =====

export async function registerUser({ name, email, password }) {
  const data = await request("/register", {
    method: "POST",
    body: JSON.stringify({ name, email, password }),
  });
  if (data.token) {
    setTokens(data.token, data.refresh_token);
  }
  return data;
}

export async function loginUser({ email, password }) {
  const data = await request("/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  if (data.token) {
    setTokens(data.token, data.refresh_token);
  }
  return data;
}

export async function logoutUser() {
  clearTokens();
  return request("/logout", { method: "POST" }, null).catch(() => null);
}

export async function getCurrentUser() {
  return request("/me", {}, accessToken);
}

export async function refreshAccessToken() {
  if (!refreshToken) {
    throw new Error("No refresh token available");
  }
  const data = await request("/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (data.token) {
    setTokens(data.token, data.refresh_token);
  }
  return data;
}

// ===== User Profile Management =====

export async function updateUserProfile({ name, email }) {
  return request("/profile", {
    method: "PUT",
    body: JSON.stringify({ name, email }),
  }, accessToken);
}

export async function changePassword({ old_password, new_password }) {
  return request("/change-password", {
    method: "POST",
    body: JSON.stringify({ old_password, new_password }),
  }, accessToken);
}

export async function deleteUserAccount() {
  return request("/account", { method: "DELETE" }, accessToken);
}

export async function getAISubscription() {
  return request("/ai-subscription", {}, accessToken);
}

// ===== Code Management =====

export async function saveCode({ title, code, language, is_public }) {
  return request("/saved-codes", {
    method: "POST",
    body: JSON.stringify({ title, code, language, is_public: is_public || false }),
  }, accessToken);
}

export async function fetchSavedCodes() {
  return request("/saved-codes", {}, accessToken);
}

export async function getCode(codeId) {
  return request(`/saved-codes/${codeId}`, {}, accessToken);
}

export async function updateCode(codeId, { title, code, is_public }) {
  return request(`/saved-codes/${codeId}`, {
    method: "PUT",
    body: JSON.stringify({ title, code, is_public }),
  }, accessToken);
}

export async function deleteCode(codeId) {
  return request(`/saved-codes/${codeId}`, { method: "DELETE" }, accessToken);
}

export async function getPublicCodes() {
  return request("/public-codes", {});
}

// ===== Code Sharing =====

export async function shareCode(codeId, { shared_with_email, permission }) {
  return request(`/saved-codes/${codeId}/share`, {
    method: "POST",
    body: JSON.stringify({ shared_with_email, permission }),
  }, accessToken);
}

export async function getSharedCodes() {
  return request("/shared-codes", {}, accessToken);
}

export async function revokeCodeAccess(codeId, userId) {
  return request(`/saved-codes/${codeId}/share/${userId}`, { method: "DELETE" }, accessToken);
}

export async function checkCodeAccess(codeId) {
  return request(`/saved-codes/${codeId}/access`, {}, accessToken).catch(() => ({
    has_access: false,
    permission: null,
  }));
}

// ===== Code Execution =====

export async function executeCode(code, { inputValue = "0", timeoutSeconds = 5, maxSteps = 2000 } = {}) {
  return request("/execute", {
    method: "POST",
    body: JSON.stringify({
      code,
      input_value: inputValue,
      timeout_seconds: timeoutSeconds,
      max_steps: maxSteps,
    }),
  });
}

// ===== AI Help =====

export async function getAIHelp({ code, question }) {
  return request("/ai-help", {
    method: "POST",
    body: JSON.stringify({ code, question }),
  }, accessToken);
}
