import React from "react";

export default function AIHelpPanel({ code, question, onQuestionChange, onAsk, onApplyCode, loading, result }) {
  return (
    <div className="ai-panel">
      <div className="panel-head">
        <span className="panel-title"><span className="dot">●</span>AI help</span>
      </div>
      <div className="ai-body">
        <textarea
          value={question}
          onChange={(e) => onQuestionChange?.(e.target.value)}
          placeholder="Ask the compiler what to fix or improve in this code..."
          rows={3}
        />
        <button className="primary-btn" onClick={onAsk} disabled={loading || (!code.trim() && !question.trim())}>
          {loading ? "Thinking..." : "Ask AI"}
        </button>
        <div className="ai-output">
          {result ? (
            <>
              <div className="ai-answer">{result.answer}</div>
              {result.generated_code && (
                <div className="ai-code-result">
                  <pre>{result.generated_code}</pre>
                  <button className="secondary-btn" onClick={() => onApplyCode?.(result.generated_code)}>
                    Apply to editor
                  </button>
                </div>
              )}
              {result.suggestions?.length > 0 && (
                <ul>
                  {result.suggestions.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              )}
            </>
          ) : (
            <div className="empty-state">Use the AI assistant for debugging help or improvement ideas.</div>
          )}
        </div>
      </div>
    </div>
  );
}
