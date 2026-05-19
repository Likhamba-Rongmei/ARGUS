import { useEffect, useRef } from "react";
import { pollStatus } from "../api/argus";

// Polls /api/status/:jobId every 1.5s until complete or error.
// Calls onComplete(jobId) or onError(msg) accordingly.
export default function StatusPoller({ jobId, onComplete, onError }) {
  const intervalRef = useRef(null);

  useEffect(() => {
    if (!jobId) return;

    intervalRef.current = setInterval(async () => {
      try {
        const { status, error } = await pollStatus(jobId);
        if (status === "complete") {
          clearInterval(intervalRef.current);
          onComplete(jobId);
        } else if (status === "error") {
          clearInterval(intervalRef.current);
          onError(error || "Pipeline failed");
        }
        // status === "queued" or "running" → keep polling
      } catch (e) {
        clearInterval(intervalRef.current);
        onError(e.message);
      }
    }, 1500);

    return () => clearInterval(intervalRef.current);
  }, [jobId]);

  return null; // purely behavioural, no UI
}
