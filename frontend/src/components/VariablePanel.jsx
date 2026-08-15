import React, { useState } from "react";
import { renderValue, shortTypeLabel } from "../utils/renderValue";

function ValueBlock({ node, addedIndices = [], removedIndices = [] }) {
  if (!node) return null;

  if (node.type === "list" || node.type === "tuple" || node.type === "set") {
    if (node.value.length === 0) {
      return <span>{node.type === "tuple" ? "()" : node.type === "set" ? "set()" : "[]"}</span>;
    }
    const open = node.type === "tuple" ? "(" : node.type === "set" ? "{" : "[";
    const close = node.type === "tuple" ? ")" : node.type === "set" ? "}" : "]";
    return (
      <span>
        {open}
        {node.value.map((item, i) => {
          const isAdded = addedIndices.includes(i);
          return (
            <React.Fragment key={i}>
              <span className={isAdded ? "token-added" : ""}>{renderValue(item)}</span>
              {i < node.value.length - 1 ? ", " : ""}
            </React.Fragment>
          );
        })}
        {close}
      </span>
    );
  }

  if (node.type === "dict") {
    if (node.value.length === 0) return <span>{"{}"}</span>;
    return (
      <span>
        {"{"}
        {node.value.map((entry, i) => (
          <React.Fragment key={i}>
            {renderValue(entry.key)}: {renderValue(entry.value)}
            {i < node.value.length - 1 ? ", " : ""}
          </React.Fragment>
        ))}
        {"}"}
      </span>
    );
  }

  return <span>{renderValue(node)}</span>;
}

function VariableCard({ name, entry }) {
  const [open, setOpen] = useState(true);
  const kind = entry.kind; // added | modified | removed | unchanged
  const current = entry.current;
  const previous = entry.previous;
  const displayNode = current || previous;

  return (
    <div className={`var-card kind-${kind}`}>
      <div className="var-card-head" onClick={() => setOpen((o) => !o)}>
        <div>
          <span className="var-name">{name}</span>
          {displayNode && <span className="var-type">{shortTypeLabel(displayNode.type)}</span>}
        </div>
        <span className={`var-badge ${kind}`}>{kind}</span>
      </div>

      {open && (
        <div className="var-card-body">
          <ValueBlock
            node={current}
            addedIndices={entry.added_indices || []}
            removedIndices={entry.removed_indices || []}
          />
          {kind === "modified" && previous && (
            <span className="var-diff-line">
              was: {renderValue(previous)}
            </span>
          )}
          {kind === "removed" && (
            <span className="var-diff-line">removed after being: {renderValue(previous)}</span>
          )}
        </div>
      )}
    </div>
  );
}

export default function VariablePanel({ currentStep, hasResult }) {
  return (
    <div className="panel panel-state">
      <div className="panel-head">
        <span className="panel-title">
          <span className="dot">●</span>Runtime State
        </span>
        {currentStep && (
          <span className="step-readout">line {currentStep.line ?? "—"}</span>
        )}
      </div>

      <div className="var-list">
        {!hasResult && (
          <div className="empty-state">Run some code to see live variable state here.</div>
        )}

        {hasResult && !currentStep && (
          <div className="empty-state">No variables yet — step forward on the timeline.</div>
        )}

        {currentStep &&
          Object.entries(currentStep.changes || {}).map(([name, entry]) => (
            <VariableCard key={name} name={name} entry={entry} />
          ))}
      </div>
    </div>
  );
}
