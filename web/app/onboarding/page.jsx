'use client';
import { useState } from 'react';
export default function Onboarding() {
  const [f, setF] = useState({ cls: 'SS2', exam: 'WAEC', lang: 'en' });
  return (<div className="bg-white border rounded-xl p-5 max-w-lg space-y-3">
    <h1 className="font-extrabold text-xl">Setup</h1>
    <label className="text-sm">Class<select value={f.cls} onChange={e => setF({ ...f, cls: e.target.value })} className="border rounded ml-2 p-1"><option>SS1</option><option>SS2</option><option>SS3</option></select></label>
    <label className="text-sm ml-3">Exam<select value={f.exam} onChange={e => setF({ ...f, exam: e.target.value })} className="border rounded ml-2 p-1"><option>WAEC</option><option>NECO</option><option>JAMB</option></select></label>
    <label className="text-sm ml-3">Lang<select value={f.lang} onChange={e => setF({ ...f, lang: e.target.value })} className="border rounded ml-2 p-1"><option value="en">English</option><option value="pcm">Pidgin</option><option value="yo">Yoruba</option><option value="ha">Hausa</option><option value="ig">Igbo</option></select></label>
    <p className="text-sm text-gray-600">Saved locally for MVP. Career guidance + subjects next.</p>
    <a href="/" className="inline-block bg-[#0E7C5B] text-white rounded-lg px-4 py-2 text-sm font-bold">Continue →</a>
  </div>);
}
