'use client';
import { useState } from 'react';

export default function SignIn() {
  const [phone, setPhone] = useState('');
  const [name, setName] = useState('');
  const [msg, setMsg] = useState('');
  const [done, setDone] = useState(typeof window !== 'undefined' && !!localStorage.getItem('edu_profile'));
  const valid = /^0[789][01]\d{8}$/.test(phone.trim());
  const save = () => {
    if (!valid) { setMsg('Enter a valid 11-digit Nigerian phone number, e.g. 0803...'); return; }
    localStorage.setItem('edu_profile', JSON.stringify({ phone: phone.trim(), name: name.trim() }));
    setDone(true); setMsg('');
  };
  const out = () => { localStorage.removeItem('edu_profile'); setDone(false); setPhone(''); setName(''); };
  return (<div className="bg-white border rounded-xl p-6 max-w-md mx-auto space-y-4">
    <div className="text-center"><p className="text-4xl">🎓</p>
      <h1 className="text-2xl font-extrabold mt-2">Welcome to AI Tutor</h1>
      <p className="text-sm text-gray-600">Your personal tutor for WAEC, NECO &amp; JAMB.</p></div>
    {!done ? (<div className="space-y-3">
      <label className="block text-sm">Your name (optional)<input value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Adaeze" className="border rounded-lg p-3 w-full mt-1" /></label>
      <label className="block text-sm">Phone number<input value={phone} onChange={e => setPhone(e.target.value)} inputMode="numeric" placeholder="0803 123 4567" className="border rounded-lg p-3 w-full mt-1" /></label>
      {msg && <p className="text-sm text-red-600">{msg}</p>}
      <button onClick={save} className="bg-[#0E7C5B] text-white rounded-lg px-4 py-3 w-full font-bold">Sign in &amp; Start Learning →</button>
      <p className="text-xs text-gray-500 text-center">Simple sign-in for now — your details stay on this device. Full accounts with OTP come later.</p>
    </div>) : (<div className="space-y-3 text-center">
      <p className="font-bold">You're signed in 🎉</p>
      <a href="/" className="inline-block bg-[#0E7C5B] text-white rounded-lg px-4 py-3 font-bold">Continue to Dashboard →</a>
      <div><button onClick={out} className="text-sm underline text-gray-600">Sign out</button></div>
    </div>)}
  </div>);
}
