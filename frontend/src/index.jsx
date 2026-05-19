import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";

// Global CSS resets + keyframes
const style = document.createElement("style");
style.textContent = `
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0d0e11; color: #fff; }
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700;800&display=swap');

  @keyframes spin {
    from { transform: rotate(0deg); }
    to   { transform: rotate(360deg); }
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.4; }
  }
`;
document.head.appendChild(style);

createRoot(document.getElementById("root")).render(<App />);
