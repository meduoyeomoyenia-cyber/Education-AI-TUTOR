'use client';
import { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { getQuestions } from '../../lib/api';
import { Loading, Empty, ErrorBox } from '../../components/states';
const EXAMS = ['All', 'WAEC', 'JAMB', 'NECO'];
function Inner() {
  const sp = useSearchParams();
  const slug = sp.get('topic_slug') || '';
  const topic = sp.get('topic') || 'Algebra: Simultaneous Equations';
  const [exam, setExam] = useState(sp.get('exam') || 'All');
  const [qs, setQs] = useState(null); const [err, setErr] = useState(false); const [i, setI] = useState(0); const [msg, setMsg] = useState('');
  const label = slug || topic;
  const load = () => { setErr(false); setI(0); setMsg('');
    getQuestions({ ...(slug ? { topic_slug: slug } : { topic }), ...(exam !== 'All' ? { exam } : {}) }).then(setQs).catch(() => setErr(true)); };
  useEffect(load, [slug, topic, exam]);
  const submit = async (ans) => {
    const r = await fetch(`${process.env.NEXT_PUBLIC_API || 'http://localhost:8000'}/attempts`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question_id: qs[i].id, answer: ans }) });
    const j = await r.json(); setMsg(j.correct ? '✅ Correct' : `❌ ${j.hint || 'Try again'}`);
    if (j.correct) setTimeout(() => { setI(i + 1); setMsg(''); }, 800);
  };
  if (err) return <ErrorBox onRetry={load} />; if (!qs) return <Loading />;
  return (<div className="space-y-3 max-w-xl">
    <div className="flex gap-2 items-center text-sm">Exam<label><select value={exam} onChange={e => setExam(e.target.value)} className="border rounded ml-2 p-1">{EXAMS.map(x => (<option key={x}>{x}</option>))}</select></label></div>
    {!qs.length ? <Empty text={exam !== 'All' ? `No ${exam} practice questions are available for this topic yet.` : `No practice questions are available for this topic yet.`} cta="Back home" href="/" /> :
    i >= qs.length ? <Empty text="Done! Topic complete." cta="Revise" href="/revision" /> :
    (() => { const q = qs[i]; return (
    <div className="bg-white border rounded-xl p-5"><p className="text-xs font-bold">{q.subject} • {q.topic} • {q.difficulty}{q.exam_style ? ` • ${q.exam_style}` : ''}</p><p className="font-bold mt-1">{q.stem}</p>
    <div className="space-y-2 mt-3">{(q.options || []).map(o => (<button key={o} onClick={() => submit(o)} className="border rounded-lg p-3 w-full text-left text-sm">{o}</button>))}</div>
    {msg && <p className="text-sm mt-3">{msg}</p>}
    <div className="flex gap-2 mt-3"><input id="ta" placeholder="Type answer or 🎙️ voice (optional)" className="border rounded-lg p-2 text-sm flex-1" /><button onClick={() => submit(document.getElementById('ta').value)} className="bg-[#0E7C5B] text-white rounded-lg px-3 text-sm font-bold">Send</button></div></div>); })()}
  </div>);
}
export default function Practice() { return (<Suspense fallback={<Loading />}><Inner /></Suspense>); }
