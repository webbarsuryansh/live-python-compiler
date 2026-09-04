import React from "react";

export default function Header({
  liveMode,
  onToggleLive,
  onRun,
  isRunning,
  onSave,
  codeTitle,
  onTitleChange,
  fontSize,
  onFontSizeChange,
  panelRatio,
  onPanelRatioChange,
}) {
  return (
    <header className="app-header">
      <div className="brand">
        <span className="brand-mark">LIVE PYTHON COMPILER</span>
        <span className="brand-sub">state-aware execution</span>
      </div>

      <div className="header-controls">
        <input
          className="title-input"
          value={codeTitle}
          onChange={(e) => onTitleChange?.(e.target.value)}
          aria-label="Script title"
        />

        {!liveMode && (
          <button className="transport-btn play" onClick={onRun} title="Run">
            {isRunning ? "…" : "▶"}
          </button>
        )}

        <button className="secondary-btn" onClick={onSave} title="Save code">
          Save
        </button>

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

      <div className="toolbar-tools">
        <label className="range-field">
          <span>Font</span>
          <input type="range" min="12" max="24" value={fontSize} onChange={(e) => onFontSizeChange?.(Number(e.target.value))} />
        </label>

        <label className="range-field">
          <span>Editor</span>
          <input type="range" min="0.8" max="2" step="0.1" value={panelRatio} onChange={(e) => onPanelRatioChange?.(Number(e.target.value))} />
        </label>
      </div>
    </header>
  );
}
