import { useCallback, useEffect, useRef, useState } from "react";
import { executeCode } from "../services/api";
import { useDebounce } from "./useDebounce";

const DEBOUNCE_MS = 500;

export function useExecution(initialCode, inputValue = "") {
  const [code, setCode] = useState(initialCode);
  const [liveMode, setLiveMode] = useState(true);
  const [result, setResult] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [runError, setRunError] = useState(null); // network/syntax-while-typing state
  const [awaitingValidCode, setAwaitingValidCode] = useState(false);

  const [stepIndex, setStepIndex] = useState(-1); // -1 = before first step
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);

  const playTimer = useRef(null);
  const inputValueRef = useRef(inputValue);
  const debouncedCode = useDebounce(code, DEBOUNCE_MS);
  const lastRunToken = useRef(0);

  useEffect(() => {
    inputValueRef.current = inputValue;
  }, [inputValue]);

  const runNow = useCallback(async (source) => {
    const token = ++lastRunToken.current;
    setIsRunning(true);
    setAwaitingValidCode(false);
    try {
      const data = await executeCode(source, { inputValue: inputValueRef.current });
      if (token !== lastRunToken.current) return; // stale response
      setResult(data);
      setRunError(null);
      setStepIndex(data.steps.length > 0 ? data.steps.length - 1 : -1);
    } catch (err) {
      if (token !== lastRunToken.current) return;
      setRunError(err.message || "Execution failed");
    } finally {
      if (token === lastRunToken.current) setIsRunning(false);
    }
  }, []);

  // Live mode: run automatically on debounced code changes.
  useEffect(() => {
    if (!liveMode) return;
    if (!debouncedCode.trim()) {
      setResult(null);
      return;
    }
    setAwaitingValidCode(true);
    runNow(debouncedCode);
  }, [debouncedCode, liveMode, runNow]);

  const runManually = useCallback(() => {
    runNow(code);
  }, [code, runNow]);

  // Playback: advance stepIndex on an interval while isPlaying.
  useEffect(() => {
    if (!isPlaying || !result || result.steps.length === 0) return;

    playTimer.current = setInterval(() => {
      setStepIndex((prev) => {
        const next = prev + 1;
        if (next >= result.steps.length) {
          setIsPlaying(false);
          return prev;
        }
        return next;
      });
    }, 900 / speed);

    return () => clearInterval(playTimer.current);
  }, [isPlaying, result, speed]);

  const play = useCallback(() => {
    if (!result || result.steps.length === 0) return;
    if (stepIndex >= result.steps.length - 1) setStepIndex(0);
    setIsPlaying(true);
  }, [result, stepIndex]);

  const pause = useCallback(() => setIsPlaying(false), []);

  const stepNext = useCallback(() => {
    setIsPlaying(false);
    setStepIndex((prev) => {
      if (!result) return prev;
      return Math.min(prev + 1, result.steps.length - 1);
    });
  }, [result]);

  const stepPrev = useCallback(() => {
    setIsPlaying(false);
    setStepIndex((prev) => Math.max(prev - 1, 0));
  }, []);

  const stop = useCallback(() => {
    setIsPlaying(false);
    setStepIndex(result && result.steps.length > 0 ? result.steps.length - 1 : -1);
  }, [result]);

  const currentStep = result && stepIndex >= 0 ? result.steps[stepIndex] : null;
  const previousStep = result && stepIndex > 0 ? result.steps[stepIndex - 1] : null;

  return {
    code,
    setCode,
    liveMode,
    setLiveMode,
    result,
    isRunning,
    runError,
    awaitingValidCode: awaitingValidCode && isRunning,
    runManually,
    stepIndex,
    setStepIndex,
    currentStep,
    previousStep,
    isPlaying,
    play,
    pause,
    stepNext,
    stepPrev,
    stop,
    speed,
    setSpeed,
  };
}
