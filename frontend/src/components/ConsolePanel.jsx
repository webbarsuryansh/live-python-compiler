import React from "react";

export default function ConsolePanel({ stdout, error, timedOut, truncated, onJumpToLine, style, inputValue, onInputValueChange, onRun, isRunning }) {
  const lines = (stdout || "").split("\n").filter((_, i, arr) => !(i === arr.length - 1 && arr[i] === ""));

  return (
    <div className="console-panel" style={style}>
      {error && (
        <div className="error-block" onClick={() => error.line && onJumpToLine?.(error.line)}>
          <div className="error-title">
            {timedOut ? "TIMEOUT" : truncated ? "STEP LIMIT" : "ERROR"} · {error.type}
          </div>
          {error.line && <div className="error-line">Line {error.line} — click to jump</div>}
          <div className="error-message">{error.message}</div>
        </div>
      )}

      <div className="panel-head">
        <span className="panel-title">
          <span className="dot">●</span>Console
        </span>
      </div>

      <div className="console-output">
        {lines.length === 0 && !error && <div className="console-empty">No output yet.</div>}
        {lines.map((line, i) => (
          <div className="console-line" key={i}>
            {line}
          </div>
        ))}
        <div className="console-terminal-line">
          <span className="console-prompt">&gt;</span>
          <textarea
            className="console-terminal-input"
            value={inputValue}
            onChange={(event) => onInputValueChange?.(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) onRun?.();
            }}
            aria-label="Console input"
            placeholder="type values here, one per line"
            rows={2}
            disabled={isRunning}
          />
        </div>
      </div>
    </div>
  );
}
