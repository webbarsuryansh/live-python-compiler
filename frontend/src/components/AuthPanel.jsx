import React, { useState } from "react";

export default function AuthPanel({ user, token, onLogin, onRegister, onLogout, loading, subscription, onUpdateProfile, onChangePassword }) {
  const [mode, setMode] = useState("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [editing, setEditing] = useState(false);
  const [profileName, setProfileName] = useState(user?.name || "");
  const [profileEmail, setProfileEmail] = useState(user?.email || "");
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setMessage("");
    try {
      if (mode === "login") {
        await onLogin({ email, password });
      } else {
        await onRegister({ name, email, password });
      }
    } catch (err) {
      setMessage(err.message || "Authentication failed.");
    }
  };

  const saveProfile = async (e) => {
    e.preventDefault();
    setMessage("");
    try {
      await onUpdateProfile({ name: profileName, email: profileEmail });
      setMessage("Profile updated.");
      setEditing(false);
    } catch (err) {
      setMessage(err.message || "Profile update failed.");
    }
  };

  const savePassword = async (e) => {
    e.preventDefault();
    setMessage("");
    try {
      await onChangePassword({ old_password: oldPassword, new_password: newPassword });
      setOldPassword("");
      setNewPassword("");
      setMessage("Password changed.");
    } catch (err) {
      setMessage(err.message || "Password change failed.");
    }
  };

  if (user && token) {
    return (
      <div className="auth-panel">
        <div className="auth-user">
          <div>
            <strong>{user.name}</strong>
            <small>{user.email}</small>
            <span className="subscription-badge">{subscription?.plan || "free"} AI · active</span>
          </div>
          <button className="secondary-btn" onClick={onLogout}>Logout</button>
        </div>
        <div className="profile-actions">
          <button className="secondary-btn" onClick={() => setEditing((value) => !value)}>
            {editing ? "Close profile" : "Manage profile"}
          </button>
        </div>
        {editing && (
          <div className="profile-forms">
            <form className="auth-form" onSubmit={saveProfile}>
              <strong>Profile</strong>
              <input value={profileName} onChange={(e) => setProfileName(e.target.value)} placeholder="Full name" />
              <input value={profileEmail} onChange={(e) => setProfileEmail(e.target.value)} placeholder="Email" type="email" />
              <button className="primary-btn" type="submit" disabled={loading}>Save profile</button>
            </form>
            <form className="auth-form" onSubmit={savePassword}>
              <strong>Password</strong>
              <input value={oldPassword} onChange={(e) => setOldPassword(e.target.value)} placeholder="Current password" type="password" />
              <input value={newPassword} onChange={(e) => setNewPassword(e.target.value)} placeholder="New password" type="password" />
              <button className="secondary-btn" type="submit" disabled={loading}>Change password</button>
            </form>
            {message && <div className="auth-message">{message}</div>}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="auth-panel">
      <div className="auth-switch">
        <button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>Login</button>
        <button className={mode === "register" ? "active" : ""} onClick={() => setMode("register")}>Register</button>
      </div>

      <form className="auth-form" onSubmit={submit}>
        {mode === "register" && (
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Full name" />
        )}
        <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" type="email" />
        <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" type="password" />
        {message && <div className="auth-message">{message}</div>}
        <button className="primary-btn" type="submit" disabled={loading}>
          {loading ? "Please wait..." : mode === "login" ? "Login" : "Create account"}
        </button>
      </form>
    </div>
  );
}
