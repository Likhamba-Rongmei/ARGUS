const BASE = "http://localhost:8000/api";

export async function uploadDocument(file) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/upload`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
  return res.json(); // { job_id, status }
}

export async function pollStatus(jobId) {
  const res = await fetch(`${BASE}/status/${jobId}`);
  if (!res.ok) throw new Error(`Status check failed: ${res.status}`);
  return res.json(); // { job_id, status, error }
}

export async function getVerdict(jobId) {
  const res = await fetch(`${BASE}/verdict/${jobId}`);
  if (!res.ok) throw new Error(`Verdict fetch failed: ${res.status}`);
  return res.json();
}

export async function getClaims(jobId) {
  const res = await fetch(`${BASE}/claims/${jobId}`);
  if (!res.ok) throw new Error(`Claims fetch failed: ${res.status}`);
  return res.json();
}

export async function getForensics(jobId) {
  const res = await fetch(`${BASE}/forensics/${jobId}`);
  if (!res.ok) throw new Error(`Forensics fetch failed: ${res.status}`);
  return res.json();
}

export async function getReconciliation(jobId) {
  const res = await fetch(`${BASE}/reconciliation/${jobId}`);
  if (!res.ok) throw new Error(`Reconciliation fetch failed: ${res.status}`);
  return res.json();
}

export async function getGraph(jobId) {
  const res = await fetch(`${BASE}/graph/${jobId}`);
  if (!res.ok) throw new Error(`Graph fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchAllResults(jobId) {
  const [verdict, claims, forensics, reconciliation, graph] = await Promise.all([
    getVerdict(jobId),
    getClaims(jobId),
    getForensics(jobId),
    getReconciliation(jobId),
    getGraph(jobId),
  ]);
  return { verdict, claims, forensics, reconciliation, graph };
}
