import { useEffect, useState } from "react";
import {
  getCurrentUser,
  loginUser,
  registerUser,
  logoutUser,
  setTokens,
  getAccessToken,
  clearTokens,
  updateUserProfile,
  changePassword,
} from "../services/api";

export function useAuth() {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("lpc_user");
    return saved ? JSON.parse(saved) : null;
  });

  const [token, setToken] = useState(() => localStorage.getItem("lpc_token") || "");
  const [refreshToken, setRefreshToken] = useState(() => localStorage.getItem("lpc_refresh_token") || "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Persist user to localStorage
  useEffect(() => {
    if (user) {
      localStorage.setItem("lpc_user", JSON.stringify(user));
    } else {
      localStorage.removeItem("lpc_user");
    }
  }, [user]);

  // Verify token on mount
  useEffect(() => {
    if (token && !user) {
      verifyToken();
    }
  }, []);

  const verifyToken = async () => {
    try {
      setLoading(true);
      const userData = await getCurrentUser();
      setUser(userData);
    } catch (err) {
      console.error("Token verification failed:", err);
      clearTokens();
      setToken("");
      setRefreshToken("");
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    setLoading(true);
    setError("");
    try {
      const response = await loginUser({ email, password });
      setTokens(response.token, response.refresh_token);
      setToken(response.token);
      setRefreshToken(response.refresh_token);
      setUser(response.user);
      return response;
    } catch (err) {
      const errorMsg = err.message || "Login failed";
      setError(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (name, email, password) => {
    setLoading(true);
    setError("");
    try {
      const response = await registerUser({ name, email, password });
      setTokens(response.token, response.refresh_token);
      setToken(response.token);
      setRefreshToken(response.refresh_token);
      setUser(response.user);
      return response;
    } catch (err) {
      const errorMsg = err.message || "Registration failed";
      setError(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    try {
      await logoutUser();
    } catch (err) {
      console.error("Logout error:", err);
    } finally {
      clearTokens();
      setToken("");
      setRefreshToken("");
      setUser(null);
      setLoading(false);
    }
  };

  const updateProfile = async (profile) => {
    setLoading(true);
    setError("");
    try {
      const updatedUser = await updateUserProfile(profile);
      setUser(updatedUser);
      return updatedUser;
    } catch (err) {
      setError(err.message || "Profile update failed");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const updatePassword = async (passwords) => {
    setLoading(true);
    setError("");
    try {
      return await changePassword(passwords);
    } catch (err) {
      setError(err.message || "Password change failed");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const isAuthenticated = !!token && !!user;

  return {
    user,
    token,
    refreshToken,
    loading,
    error,
    isAuthenticated,
    login,
    register,
    logout,
    updateProfile,
    updatePassword,
    setError,
    verifyToken,
  };
}
