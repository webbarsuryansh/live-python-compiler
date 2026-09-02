import React, { useEffect, useState } from "react";
import Header from "./components/Header";
import EditorPanel from "./components/EditorPanel";
import VariablePanel from "./components/VariablePanel";
import Timeline from "./components/Timeline";
import ConsolePanel from "./components/ConsolePanel";
import AuthPanel from "./components/AuthPanel";
import AIHelpPanel from "./components/AIHelpPanel";
import { useExecution } from "./hooks/useExecution";
import { useAuth } from "./hooks/useAuth";
import { fetchSavedCodes, saveCode, getAIHelp, getAISubscription } from "./services/api";

const SAMPLE_CODE = `import math
numbers = [4, 9, 16, 25]
print([math.sqrt(n) for n in numbers])
`;

export default function App() {
  const [inputValue, setInputValue] = useState("0");
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
  } = useExecution(SAMPLE_CODE, inputValue);

  // Use the new auth hook
  const auth = useAuth();

  const [jumpToLine, setJumpToLine] = useState(null);
  const [editorFontSize, setEditorFontSize] = useState(14);
  const [panelRatio, setPanelRatio] = useState(1.3);
  const [bottomRatio, setBottomRatio] = useState(1);
  const [workspaceHeight, setWorkspaceHeight] = useState(420);
  const [consoleHeight, setConsoleHeight] = useState(160);
  const [resizeState, setResizeState] = useState(null);
  const [savedCodes, setSavedCodes] = useState([]);
  const [codeTitle, setCodeTitle] = useState("demo.py");
  const [appError, setAppError] = useState("");
  const [aiQuestion, setAiQuestion] = useState("");
  const [aiResult, setAiResult] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiSubscription, setAiSubscription] = useState(null);

  useEffect(() => {
    if (!resizeState) return undefined;

    const handlePointerMove = (event) => {
      if (resizeState.type === "workspace") {
        const ratio = event.clientX / window.innerWidth;
        setPanelRatio(Math.min(4, Math.max(0.35, ratio / (1 - ratio))));
      } else if (resizeState.type === "bottom") {
        const ratio = (event.clientX - 16) / Math.max(1, window.innerWidth - 32);
        setBottomRatio(Math.min(4, Math.max(0.35, ratio / (1 - ratio))));
      } else if (resizeState.type === "console") {
        setConsoleHeight(Math.min(window.innerHeight * 0.6, Math.max(90, window.innerHeight - event.clientY)));
      } else if (resizeState.type === "workspace-height") {
        setWorkspaceHeight(Math.min(window.innerHeight * 0.7, Math.max(180, event.clientY - resizeState.top)));
      }
    };

    const stopResizing = () => setResizeState(null);
    document.body.classList.add("is-resizing");
    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", stopResizing);
    return () => {
      document.body.classList.remove("is-resizing");
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", stopResizing);
    };
  }, [resizeState]);

  const isSyntaxWaiting = result && !result.success && result.error?.type === "SyntaxError";
  const errorLine = result?.error?.line ?? null;

  // Fetch saved codes when user logs in
  useEffect(() => {
    if (auth.isAuthenticated) {
      fetchSavedCodes()
        .then((data) => setSavedCodes(data || []))
        .catch((err) => {
          console.error("Failed to fetch saved codes:", err);
          setSavedCodes([]);
        });
      getAISubscription().then(setAiSubscription).catch(() => setAiSubscription(null));
    } else {
      setSavedCodes([]);
      setAiSubscription(null);
    }
  }, [auth.isAuthenticated]);

  const handleLogin = async (credentials) => {
    try {
      await auth.login(credentials.email, credentials.password);
      setAppError("");
    } catch (error) {
      setAppError(error.message || "Login failed");
      throw error;
    }
  };

  const handleRegister = async (credentials) => {
    try {
      await auth.register(credentials.name, credentials.email, credentials.password);
      setAppError("");
    } catch (error) {
      setAppError(error.message || "Registration failed");
      throw error;
    }
  };

  const handleLogout = async () => {
    await auth.logout();
    setAppError("");
    setSavedCodes([]);
  };

  const handleSaveCode = async () => {
    if (!auth.isAuthenticated) {
      setAppError("Please log in before saving code.");
      return;
    }

    try {
      const saved = await saveCode({
        title: codeTitle || "Untitled script",
        code,
        language: "python",
        is_public: false,
      });
      setSavedCodes((prev) => [saved, ...prev]);
      setAppError("");
    } catch (error) {
      setAppError(error.message || "Could not save code");
    }
  };

  const handleAiHelp = async () => {
    setAiLoading(true);
    setAiResult(null);
    try {
      const response = await getAIHelp({ code, question: aiQuestion });
      setAiResult(response);
    } catch (error) {
      setAiResult({
        answer: error.message || "AI help is unavailable right now.",
        suggestions: [],
        generated_code: null,
        is_local_fallback: true,
      });
    } finally {
      setAiLoading(false);
    }
  };

  const handleApplyAiCode = (generatedCode) => {
    setCode(generatedCode);
    setCodeTitle("ai-generated.py");
    setAppError("");
  };

  const handleLoadCode = (entry) => {
    setCode(entry.code);
    setCodeTitle(entry.title);
  };

  // Combine errors
  const displayError = appError || auth.error || runError;

  return (
    <div className="app-shell">
      <Header
        liveMode={liveMode}
        onToggleLive={setLiveMode}
        onRun={runManually}
        isRunning={isRunning}
        onSave={handleSaveCode}
        codeTitle={codeTitle}
        onTitleChange={setCodeTitle}
        fontSize={editorFontSize}
        onFontSizeChange={setEditorFontSize}
        panelRatio={panelRatio}
        onPanelRatioChange={setPanelRatio}
        inputValue={inputValue}
        onInputValueChange={setInputValue}
      />

      {isSyntaxWaiting && <div className="waiting-banner">Waiting for valid Python…</div>}
      {displayError && <div className="waiting-banner">{displayError}</div>}

      <div className="workspace" style={{ "--editor-ratio": panelRatio, height: `${workspaceHeight}px` }}>
        <EditorPanel
          code={code}
          onChange={setCode}
          currentStep={currentStep}
          errorLine={errorLine}
          runtimeSource={result?.runtime_source}
          jumpToLine={jumpToLine}
          fontSize={editorFontSize}
        />
        <ResizeHandle orientation="vertical" label="Resize editor and variables" onPointerDown={() => setResizeState({ type: "workspace" })} />
        <VariablePanel currentStep={currentStep} hasResult={!!result && result.steps.length > 0} />
      </div>

      <ResizeHandle
        orientation="horizontal"
        label="Resize Python editor height"
        onPointerDown={(event) => {
          const workspace = event.currentTarget.previousElementSibling;
          setResizeState({
            type: "workspace-height",
            top: workspace.getBoundingClientRect().top,
          });
        }}
      />

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

      <div className="bottom-layout" style={{ "--bottom-ratio": bottomRatio }}>
        <AIHelpPanel
          code={code}
          question={aiQuestion}
          onQuestionChange={setAiQuestion}
          onAsk={handleAiHelp}
          onApplyCode={handleApplyAiCode}
          loading={aiLoading}
          result={aiResult}
        />

        <ResizeHandle orientation="vertical" label="Resize help and account panels" onPointerDown={() => setResizeState({ type: "bottom" })} />
        <div className="secondary-column">
          <AuthPanel
            user={auth.user}
            token={auth.token}
            onLogin={handleLogin}
            onRegister={handleRegister}
            onLogout={handleLogout}
            loading={auth.loading}
            subscription={aiSubscription}
            onUpdateProfile={auth.updateProfile}
            onChangePassword={auth.updatePassword}
          />

          <div className="saved-panel">
            <div className="panel-head saved-head">
              <span className="panel-title">
                <span className="dot">●</span>Saved scripts
              </span>
            </div>
            <div className="saved-list">
              {savedCodes.length === 0 ? (
                <div className="empty-state">Login and save a snippet to keep it here.</div>
              ) : (
                savedCodes.map((entry) => (
                  <button key={entry.id} className="saved-item" onClick={() => handleLoadCode(entry)}>
                    <strong>{entry.title}</strong>
                    <span>{new Date(entry.updated_at).toLocaleDateString()}</span>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      <ResizeHandle orientation="horizontal" label="Resize console" onPointerDown={() => setResizeState({ type: "console" })} />
      <ConsolePanel
        style={{ flexBasis: `${consoleHeight}px` }}
        stdout={currentStep ? accumulateStdout(result, stepIndex) : ""}
        error={result?.error}
        timedOut={result?.timed_out}
        truncated={result?.truncated}
        onJumpToLine={(line) => setJumpToLine({ line, t: Date.now() })}
      />
    </div>
  );
}

function ResizeHandle({ orientation, label, onPointerDown }) {
  return (
    <button
      type="button"
      className={`resize-handle resize-handle-${orientation}`}
      aria-label={label}
      title={label}
      onPointerDown={(event) => {
        event.preventDefault();
        onPointerDown(event);
      }}
    />
  );
}

function accumulateStdout(result, upToStepIndex) {
  if (!result) return "";
  let out = "";
  for (let i = 0; i <= upToStepIndex && i < result.steps.length; i++) {
    out += result.steps[i].stdout_delta || "";
  }
  return out;
}
