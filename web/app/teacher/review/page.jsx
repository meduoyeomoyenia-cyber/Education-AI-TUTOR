'use client';
import { useEffect, useState, Suspense } from 'react';
import { Loading, Empty, ErrorBox } from '../../../components/states';
const API = process.env.NEXT_PUBLIC_API || 'http://localhost:8000';
async function api(path, opts) {
  const r = await fetch(`${API}${path}`, { cache: 'no-store', headers: { 'Content-Type': 'application/json' }, ...opts });
  if (!r.ok) throw new Error('api failed'); return r.json();
}
function Inner() {
  const [items, setItems] = useState(null); const [err, setErr] = useState(false);
  const [filter, setFilter] = useState('PENDING'); const [notes, setNotes] = useState({});
  const load = () => { setErr(false);
    const p = filter === 'ALL' ? '/question-imports' : '/question-imports?status=' + filter;
    api(p).then(setItems).catch(() => setErr(true)); };
  useEffect(load, [filter]);
  const act = async (id, action) => {
    await api(`/question-imports/${id}/${action}`, { method: 'POST', body: JSON.stringify({ reviewer_notes: notes[id] || '' }) });
    load();
  };
  const pending = (items || []).filter(i => ['IMPORTED', 'NEEDS_REVIEW', 'NEEDS_REVISION'].includes(i.status));
  const shown = filter === 'PENDING' ? pending : (items || []);
  if (err) return <ErrorBox onRetry={load} />; if (!items) return <Loading />;
  return (<div className="space-y-4 max-w-2xl">
    <h1 className="text-2xl font-extrabold">Teacher Review (prototype, no login)</h1>
    <div className="flex gap-2 text-sm">{['PENDING', 'ALL', 'APPROVED', 'REJECTED'].map(f => (<button key={f} onClick={() => setFilter(f)} className={`border rounded-full px-3 py-1 ${filter === f ? 'bg-black text-white' : 'bg-white'}`}>{f}</button>))}</div>
    {shown.length === 0 && <Empty text="No staged questions." cta="Back home" href="/" />}
    {shown.map(q => (<div key={q.id} className="bg-white border rounded-xl p-4 space-y-2">
      <p className="text-xs font-bold">{q.subject} • {q.topic} • {q.exam_style} • {q.difficulty} • {q.source}</p>
      <p className="font-bold">{q.question_text}</p>
      {(q.options || []).length > 0 && <ul className="list-disc ml-5 text-sm">{q.options.map(o => (<li key={o}>{o}{o === q.answer ? ' ✓' : ''}</li>))}</ul>}
      <p className="text-sm">Answer: {q.answer}</p>
      {q.explanation && <p className="text-sm text-gray-600">Why: {q.explanation}</p>}
      <p className="text-xs">Validation: <b>{q.validation_status}</b> — {q.validation_notes}</p>
      <p className="text-xs">Status: <b>{q.status}</b>{q.reviewer_notes ? ` — reviewer: ${q.reviewer_notes}` : ''}</p>
      <input placeholder="Reviewer notes (optional)" value={notes[q.id] || ''} onChange={e => setNotes({ ...notes, [q.id]: e.target.value })} className="border rounded-lg p-2 text-sm w-full" />
      <div className="flex gap-2">
        <button onClick={() => act(q.id, 'approve')} className="bg-[#0E7C5B] text-white rounded-lg px-3 py-1 text-sm font-bold">Approve</button>
        <button onClick={() => act(q.id, 'revision')} className="border rounded-lg px-3 py-1 text-sm">Needs Revision</button>
        <button onClick={() => act(q.id, 'reject')} className="border rounded-lg px-3 py-1 text-sm">Reject</button>
      </div>
    </div>))}
  </div>);
}
export default function Review() { return (<Suspense fallback={<Loading />}><Inner /></Suspense>); }
