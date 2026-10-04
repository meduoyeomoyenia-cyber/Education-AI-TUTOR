'use client';
import { useEffect, useState } from 'react';
import { getSubjects, getTopics, getSyllabus } from '../lib/api';
import { Loading, Empty, ErrorBox, OfflineBar, LangToggle, DataSaver } from '../components/states';
export default function Home() {
  const [data, setData] = useState(null); const [err, setErr] = useState(false);
  const [lang, setLang] = useState('en'); const [saver, setSaver] = useState(true);
  const [offline, setOffline] = useState(false);
  const [subjects, setSubjects] = useState(['Mathematics']);
  const [subject, setSubject] = useState('Mathematics');
  const load = () => {
    setErr(false);
    // Slug links for migrated topics; ?topic= alias fallback from syllabus nodes
    // so unmigrated subjects still list their topics (no content generated).
    Promise.all([getTopics({ subject }), getSyllabus({ subject })]).then(([ts, nodes]) => {
      const byTitle = new Map();
      (ts || []).forEach(t => byTitle.set(t.title, { title: t.title, slug: t.slug }));
      (nodes || []).forEach(n => { if (!byTitle.has(n.topic)) byTitle.set(n.topic, { title: n.topic, slug: null }); });
      setData([...byTitle.values()]);
    }).catch(() => setErr(true));
  };
  useEffect(() => { getSubjects().then(ss => { if (ss.length) { setSubjects(ss); if (!ss.includes(subject)) setSubject(ss[0]); } }).catch(() => {}); }, []);
  useEffect(load, [subject]);
  useEffect(() => { setOffline(!navigator.onLine); const f = () => setOffline(!navigator.onLine); window.addEventListener('online', f); window.addEventListener('offline', f); return () => { window.removeEventListener('online', f); window.removeEventListener('offline', f); }; }, []);
  const link = (t, page) => `/${page}?${t.slug ? `topic_slug=${encodeURIComponent(t.slug)}` : `topic=${encodeURIComponent(t.title)}`}`;
  return (<div className="space-y-4">
    <div className="flex justify-between items-center flex-wrap gap-2"><h1 className="text-2xl font-extrabold">Good morning! Today: {subject}</h1><DataSaver on={saver} setOn={setSaver} /></div>
    <div className="flex gap-2 flex-wrap items-center">
      <label className="text-sm">Subject<select value={subject} onChange={e => setSubject(e.target.value)} className="border rounded ml-2 p-1">{subjects.map(s => (<option key={s} value={s}>{s}</option>))}</select></label>
    </div>
    <LangToggle lang={lang} setLang={setLang} />
    {offline && <OfflineBar />}
    {err ? <ErrorBox onRetry={load} /> : !data ? <Loading /> : data.length === 0 ? <Empty text={`No topics for ${subject} yet.`} cta="Start practice" href="/practice" /> : (
      <div className="grid md:grid-cols-3 gap-3">{data.slice(0, 12).map(t => (<div key={t.slug || t.title} className="bg-white border rounded-xl p-4"><p className="text-xs font-bold text-green-700">{subject}{t.slug ? '' : ' • syllabus'}</p><p className="font-bold">{t.title}</p><div className="flex gap-3 mt-1"><a className="text-sm underline" href={link(t, 'lesson')}>Read Lesson →</a><a className="text-sm underline" href={link(t, 'practice')}>Practice →</a></div></div>))}</div>)}
    <p className="text-xs text-gray-500">Voice input optional everywhere. Academic terms stay in English. {saver ? 'Data Saver: text-first.' : ''}</p>
  </div>);
}
