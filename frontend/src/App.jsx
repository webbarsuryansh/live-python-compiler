import React, { useState } from "react";
import Header from "./components/Header";
import EditorPanel from "./components/EditorPanel";
import VariablePanel from "./components/VariablePanel";
import Timeline from "./components/Timeline";
import ConsolePanel from "./components/ConsolePanel";
import { useExecution } from "./hooks/useExecution";

const SAMPLE_CODE = `lst = [10, 20, 30, 50]
lst.append(50)
print(lst)
`;

export default function App() {
  const {
    code,
    setCode,
    liveMode,
    setLiveMode,
    result,
    isRunning,
    runError,
    runManually,
    stepIndex,
    setStepIndex,
    currentStep,
    isPlaying,
    play,
    pause,
    stepNext,
    stepPrev,
    stop,
    speed,
    setSpeed,
  } = useExecution(SAMPLE_CODE);

  const [jumpToLine, setJumpToLine] = useState(null);

  const isSyntaxWaiting = result && !result.success && result.error?.type === "SyntaxError";
  const errorLine = result?.error?.line ?? null;

  return (
    <div className="app-shell">
      <Header
        liveMode={liveMode}
        onToggleLive={setLiveMode}
        onRun={runManually}
        isRunning={isRunning}
      />

      {isSyntaxWaiting && <div className="waiting-banner">Waiting for valid Python…</div>}
      {runError && <div className="waiting-banner">{runError}</div>}

      <div className="workspace">
        <EditorPanel
          code={code}
          onChange={setCode}
          currentStep={currentStep}
          errorLine={errorLine}
          runtimeSource={result?.runtime_source}
          jumpToLine={jumpToLine}
        />
        <VariablePanel currentStep={currentStep} hasResult={!!result && result.steps.length > 0} />
      </div>

      <Timeline
        steps={result?.steps || []}
        stepIndex={stepIndex}
        onSelect={setStepIndex}
        isPlaying={isPlaying}
        onPlay={play}
        onPause={pause}
        onNext={stepNext}
        onPrev={stepPrev}
        onStop={stop}
        speed={speed}
        onSpeedChange={setSpeed}
      />

      <ConsolePanel
        stdout={currentStep ? accumulateStdout(result, stepIndex) : ""}
        error={result?.error}
        timedOut={result?.timed_out}
        truncated={result?.truncated}
        onJumpToLine={(line) => setJumpToLine({ line, t: Date.now() })}
      />
    </div>
  );
}

// The console should only show output produced up to the currently
// scrubbed-to step, so stepping backward on the timeline also rewinds
// what's shown in the console — reinforcing the "watch state evolve" idea.
function accumulateStdout(result, upToStepIndex) {
  if (!result) return "";
  let out = "";
  for (let i = 0; i <= upToStepIndex && i < result.steps.length; i++) {
    out += result.steps[i].stdout_delta || "";
  }
  return out;
}
