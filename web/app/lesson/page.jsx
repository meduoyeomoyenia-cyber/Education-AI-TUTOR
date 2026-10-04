'use client';
import { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { getLesson } from '../../lib/api';
import { Loading, Empty, ErrorBox } from '../../components/states';
function Inner() {
  const sp = useSearchParams(); const slug = sp.get('topic_slug') || ''; const topic = sp.get('topic') || '';
  const [ls, setLs] = useState(null); const [err, setErr] = useState(false);
  const load = () => { setErr(false); getLesson(slug ? { topic_slug: slug } : { topic }).then(setLs).catch(() => setErr(true)); };
  useEffect(load, [slug, topic]);
  if (err) return <ErrorBox onRetry={load} />; if (!ls) return <Loading />;
  if (ls.error) return <Empty text={`No lesson yet for ${slug || topic}.`} cta="Practice instead" href={`/practice?${slug ? `topic_slug=${encodeURIComponent(slug)}` : `topic=${encodeURIComponent(topic)}`}`} />;
  return (<article className="bg-white border rounded-xl p-5 max-w-2xl space-y-4">
    <div><p className="text-xs font-bold text-green-700">{ls.subject} • {ls.class} • {ls.reading_mins} min read</p>
      <h1 className="text-2xl font-extrabold">{ls.title}</h1></div>
    <section><h2 className="font-extrabold text-sm">Objectives</h2><ul className="list-disc ml-5 text-sm space-y-1">{ls.objectives.map(o => (<li key={o}>{o}</li>))}</ul></section>
    <section><h2 className="font-extrabold text-sm">Explanation</h2><p className="text-sm leading-relaxed">{ls.explanation}</p></section>
    <section className="space-y-3"><h2 className="font-extrabold text-sm">Worked examples</h2>{ls.examples.map(e => (
      <div key={e.title} className="border rounded-lg p-3"><p className="font-bold text-sm">{e.title}</p>
        <ol className="list-decimal ml-5 text-sm space-y-1">{e.steps.map(s => (<li key={s}>{s}</li>))}</ol>
        <p className="text-sm mt-1 font-bold">Answer: {e.answer}</p></div>))}</section>
    <section><h2 className="font-extrabold text-sm">Key points</h2><ul className="list-disc ml-5 text-sm space-y-1">{ls.key_points.map(k => (<li key={k}>{k}</li>))}</ul></section>
    {(ls.media || []).length > 0 && (<section><h2 className="font-extrabold text-sm">Media</h2>{ls.media.map((m, i) => (<p key={i} className="text-sm">{m.kind}: {m.caption}</p>))}</section>)}
    <a href={`/practice?${ls.topic_slug ? `topic_slug=${encodeURIComponent(ls.topic_slug)}` : `topic=${encodeURIComponent(ls.topic)}`}`} className="inline-block bg-[#0E7C5B] text-white rounded-lg px-4 py-2 text-sm font-bold">Practice this topic →</a>
  </article>);
}
export default function Lesson() { return (<Suspense fallback={<Loading />}><Inner /></Suspense>); }
