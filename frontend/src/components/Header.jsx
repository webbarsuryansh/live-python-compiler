import React from "react";

export default function Header({ liveMode, onToggleLive, onRun, isRunning }) {
  return (
    <header className="app-header">
      <div className="brand">
        <span className="brand-mark">LIVE PYTHON COMPILER</span>
        <span className="brand-sub">state-aware execution</span>
      </div>

      <div className="header-controls">
        {!liveMode && (
          <button className="transport-btn play" onClick={onRun} title="Run">
            {isRunning ? "…" : "▶"}
          </button>
        )}

        <button
          className={`live-pill ${liveMode ? "on" : ""}`}
          onClick={() => onToggleLive(!liveMode)}
          title="Toggle live execution"
        >
          <span className="live-dot" />
          Live execution {liveMode ? "on" : "off"}
        </button>

        <div
          className={`toggle-switch ${liveMode ? "on" : ""}`}
          onClick={() => onToggleLive(!liveMode)}
          role="switch"
          aria-checked={liveMode}
        >
          <div className="toggle-knob" />
        </div>
      </div>
    </header>
  );
}
