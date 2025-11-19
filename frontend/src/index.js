import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

// Suppress ResizeObserver loop errors (harmless console spam)
const resizeObserverLoopErrRe = /^[^(ResizeObserver loop limit exceeded)]/;
const resizeObserverLoopErr = /^ResizeObserver loop completed with undelivered notifications/;
const originalError = console.error;
console.error = function filterWarnings(...args) {
  const firstArg = args[0];
  if (
    typeof firstArg === 'string' &&
    (resizeObserverLoopErrRe.test(firstArg) === false || 
     resizeObserverLoopErr.test(firstArg))
  ) {
    return;
  }
  originalError.apply(console, args);
};

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
