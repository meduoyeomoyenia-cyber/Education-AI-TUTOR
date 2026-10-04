export const API = process.env.NEXT_PUBLIC_API || 'http://localhost:8000';
export async function getSyllabus(p = {}) {
  const q = new URLSearchParams(p).toString();
  const r = await fetch(`${API}/syllabus?${q}`, { cache: 'no-store' });
  if (!r.ok) throw new Error('syllabus failed'); return r.json();
}
export async function getQuestions(p = {}) {
  const q = new URLSearchParams(p).toString();
  const r = await fetch(`${API}/questions?${q}`, { cache: 'no-store' });
  if (!r.ok) throw new Error('questions failed'); return r.json();
}
export async function getLesson(p = {}) {
  const q = new URLSearchParams(p).toString();
  const r = await fetch(`${API}/lessons?${q}`, { cache: 'no-store' });
  if (!r.ok) throw new Error('lesson failed'); return r.json();
}
export async function getSubjects(p = {}) {
  const q = new URLSearchParams(p).toString();
  const r = await fetch(`${API}/subjects?${q}`, { cache: 'no-store' });
  if (!r.ok) throw new Error('subjects failed'); return r.json();
}
export async function getTopics(p = {}) {
  const q = new URLSearchParams(p).toString();
  const r = await fetch(`${API}/topics?${q}`, { cache: 'no-store' });
  if (!r.ok) throw new Error('topics failed'); return r.json();
}
