import React from "react";

const SPEEDS = [0.5, 1, 2, 5];

export default function Timeline({
  steps,
  stepIndex,
  onSelect,
  isPlaying,
  onPlay,
  onPause,
  onNext,
  onPrev,
  onStop,
  speed,
  onSpeedChange,
}) {
  const total = steps?.length || 0;

  return (
    <div className="timeline-bar">
      <div className="timeline-controls">
        <button className="transport-btn" onClick={onPrev} disabled={stepIndex <= 0} title="Previous step">
          ⏮
        </button>
        {isPlaying ? (
          <button className="transport-btn play" onClick={onPause} title="Pause">
            ⏸
          </button>
        ) : (
          <button className="transport-btn play" onClick={onPlay} disabled={total === 0} title="Play">
            ▶
          </button>
        )}
        <button
          className="transport-btn"
          onClick={onNext}
          disabled={stepIndex >= total - 1}
          title="Next step"
        >
          ⏭
        </button>
        <button className="transport-btn" onClick={onStop} disabled={total === 0} title="Stop / jump to end">
          ⏹
        </button>

        <span className="step-readout">
          Step {total > 0 ? stepIndex + 1 : 0} / {total}
        </span>

        <select
          className="speed-select"
          value={speed}
          onChange={(e) => onSpeedChange(Number(e.target.value))}
        >
          {SPEEDS.map((s) => (
            <option key={s} value={s}>
              {s}x
            </option>
          ))}
        </select>
      </div>

      <div className="timeline-track">
        {steps.map((s, i) => (
          <button
            key={i}
            className={`timeline-node ${i === stepIndex ? "active" : ""}`}
            onClick={() => onSelect(i)}
            title={s.code}
          >
            <span className="bullet" />
            L{s.line ?? "?"} · {s.code.trim().slice(0, 22) || s.event}
          </button>
        ))}
      </div>
    </div>
  );
}
