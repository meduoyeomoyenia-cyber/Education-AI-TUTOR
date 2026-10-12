export const API = 'https://education-ai-tutor-1-i00t.onrender.com';

export function authHeaders() {
  if (typeof window === 'undefined') return {};
  const t = localStorage.getItem('edu_token');
  return t ? { Authorization: `Bearer ${t}` } : {};
}

async function apiGet(path, label) {
  const r = await fetch(`${API}${path}`, { cache: 'no-store', headers: authHeaders() });
  if (r.status === 401 && typeof window !== 'undefined') { window.location = '/signin'; throw new Error('signin'); }
  if (!r.ok) throw new Error(label + ' failed'); return r.json();
}

export async function apiPost(path, body) {
  const r = await fetch(`${API}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json', ...authHeaders() }, body: JSON.stringify(body) });
  if (r.status === 401 && typeof window !== 'undefined') { window.location = '/signin'; throw new Error('signin'); }
  return r.json();
}

export async function getSyllabus(p = {}) {
  return apiGet(`/syllabus?${new URLSearchParams(p).toString()}`, 'syllabus');
}
export async function getQuestions(p = {}) {
  return apiGet(`/questions?${new URLSearchParams(p).toString()}`, 'questions');
}
export async function getLesson(p = {}) {
  return apiGet(`/lessons?${new URLSearchParams(p).toString()}`, 'lesson');
}
export async function getSubjects(p = {}) {
  return apiGet(`/subjects?${new URLSearchParams(p).toString()}`, 'subjects');
}
export async function getTopics(p = {}) {
  return apiGet(`/topics?${new URLSearchParams(p).toString()}`, 'topics');
}
