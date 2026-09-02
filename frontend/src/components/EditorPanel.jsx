import React, { useEffect, useRef, useState } from "react";
import Editor from "@monaco-editor/react";

export default function EditorPanel({
  code,
  onChange,
  currentStep,
  errorLine,
  runtimeSource,
  jumpToLine,
  fontSize = 14,
}) {
  const editorOptions = {
    fontFamily: "'JetBrains Mono', monospace",
    fontSize,
    minimap: { enabled: true },
    lineNumbers: "on",
    folding: true,
    automaticLayout: true,
    scrollBeyondLastLine: false,
    smoothScrolling: true,
    cursorBlinking: "smooth",
    padding: { top: 12 },
  };
  const [view, setView] = useState("original"); // "original" | "runtime"
  const editorRef = useRef(null);
  const monacoRef = useRef(null);
  const decorationsRef = useRef([]);

  const handleMount = (editor, monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
    monaco.editor.defineTheme("neon-void", {
      base: "vs-dark",
      inherit: true,
      rules: [
        { token: "comment", foreground: "536178", fontStyle: "italic" },
        { token: "keyword", foreground: "b06bff" },
        { token: "number", foreground: "3ef7a1" },
        { token: "string", foreground: "ffc857" },
      ],
      colors: {
        "editor.background": "#0b0f16",
        "editor.lineHighlightBackground": "#121a2860",
        "editorLineNumber.foreground": "#3a4459",
        "editorCursor.foreground": "#2ee6ff",
        "editor.selectionBackground": "#2ee6ff33",
      },
    });
    monaco.editor.setTheme("neon-void");
  };

  // Highlight the currently executing line.
  useEffect(() => {
    const editor = editorRef.current;
    const monaco = monacoRef.current;
    if (!editor || !monaco || view !== "original") return;

    const decorations = [];
    if (currentStep?.line) {
      decorations.push({
        range: new monaco.Range(currentStep.line, 1, currentStep.line, 1),
        options: {
          isWholeLine: true,
          className: "current-line-highlight",
          glyphMarginClassName: "current-line-glyph",
        },
      });
    }
    decorationsRef.current = editor.deltaDecorations(decorationsRef.current, decorations);
  }, [currentStep, view]);

  // Push error markers.
  useEffect(() => {
    const editor = editorRef.current;
    const monaco = monacoRef.current;
    if (!editor || !monaco) return;
    const model = editor.getModel();
    if (!model) return;

    if (errorLine) {
      monaco.editor.setModelMarkers(model, "live-python", [
        {
          startLineNumber: errorLine,
          endLineNumber: errorLine,
          startColumn: 1,
          endColumn: model.getLineMaxColumn(errorLine),
          message: "Execution error on this line",
          severity: monaco.MarkerSeverity.Error,
        },
      ]);
    } else {
      monaco.editor.setModelMarkers(model, "live-python", []);
    }
  }, [errorLine]);

  // Jump the editor cursor to a specific line on demand (e.g. clicking an error).
  useEffect(() => {
    const editor = editorRef.current;
    if (!editor || !jumpToLine?.line) return;
    editor.revealLineInCenter(jumpToLine.line);
    editor.setPosition({ lineNumber: jumpToLine.line, column: 1 });
    setView("original");
  }, [jumpToLine]);

  return (
    <div className="panel panel-editor">
      <div className="panel-head">
        <span className="panel-title">
          <span className="dot">●</span>Python Editor
        </span>
        <div className="source-toggle">
          <button className={view === "original" ? "active" : ""} onClick={() => setView("original")}>
            Original
          </button>
          <button className={view === "runtime" ? "active" : ""} onClick={() => setView("runtime")}>
            Runtime
          </button>
        </div>
      </div>

      {view === "original" ? (
        <div className="editor-body">
          <Editor
            language="python"
            value={code}
            onChange={(v) => onChange(v ?? "")}
            onMount={handleMount}
            options={editorOptions}
            theme="neon-void"
          />
        </div>
      ) : (
        <pre className="runtime-view">
{runtimeSource || "// Run your code to see the runtime state representation"}
        </pre>
      )}
    </div>
  );
}
