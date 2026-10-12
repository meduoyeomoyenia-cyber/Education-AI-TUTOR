'use client';
import { useState } from 'react';
const API = process.env.NEXT_PUBLIC_API || 'http://localhost:8000';

export default function SignIn() {
  const [step, setStep] = useState(typeof window !== 'undefined' && localStorage.getItem('edu_token') ? 'done' : 'phone');
  const [phone, setPhone] = useState('');
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [msg, setMsg] = useState('');
  const [busy, setBusy] = useState(false);
  const post = async (path, body) => {
    const r = await fetch(`${API}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    return r.json();
  };
  const sendCode = async () => {
    setBusy(true); setMsg('');
    const j = await post('/auth/request', { phone }).catch(() => ({ error: 'Network error. Is the backend running?' }));
    setBusy(false);
    if (j.error) { setMsg(j.error); return; }
    if (j.dev_code) setMsg(`Code sent! (testing mode — your code is ${j.dev_code})`);
    else setMsg('Code sent by SMS! Enter it below.');
    setStep('code');
  };
  const verify = async () => {
    setBusy(true); setMsg('');
    const j = await post('/auth/verify', { phone, code, name }).catch(() => ({ error: 'Network error.' }));
    setBusy(false);
    if (j.error) { setMsg(j.error); return; }
    localStorage.setItem('edu_token', j.token);
    localStorage.setItem('edu_profile', JSON.stringify(j.profile));
    setStep('done');
  };
  const out = () => { localStorage.removeItem('edu_token'); localStorage.removeItem('edu_profile'); setStep('phone'); setCode(''); setMsg(''); };
  return (<div className="bg-white border rounded-xl p-6 max-w-md mx-auto space-y-4">
    <div className="text-center"><p className="text-4xl">🎓</p>
      <h1 className="text-2xl font-extrabold mt-2">Welcome to AI Tutor</h1>
      <p className="text-sm text-gray-600">Sign in with an OTP code sent to your phone.</p></div>
    {step === 'phone' && (<div className="space-y-3">
      <label className="block text-sm">Your name (optional)<input value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Adaeze" className="border rounded-lg p-3 w-full mt-1" /></label>
      <label className="block text-sm">Phone number<input value={phone} onChange={e => setPhone(e.target.value)} inputMode="numeric" placeholder="0803 123 4567" className="border rounded-lg p-3 w-full mt-1" /></label>
      {msg && <p className="text-sm text-red-600">{msg}</p>}
      <button onClick={sendCode} disabled={busy} className="bg-[#0E7C5B] text-white rounded-lg px-4 py-3 w-full font-bold">{busy ? 'Sending…' : 'Send me a code →'}</button>
    </div>)}
    {step === 'code' && (<div className="space-y-3">
      <p className="text-sm">Enter the 6-digit code sent to <b>{phone}</b> <button onClick={() => setStep('phone')} className="underline text-xs">change</button></p>
      <input value={code} onChange={e => setCode(e.target.value)} inputMode="numeric" maxLength={6} placeholder="••••••" className="border rounded-lg p-3 w-full text-center text-2xl tracking-widest" />
      {msg && <p className="text-sm text-green-700">{msg}</p>}
      <button onClick={verify} disabled={busy} className="bg-[#0E7C5B] text-white rounded-lg px-4 py-3 w-full font-bold">{busy ? 'Checking…' : 'Verify & Sign in →'}</button>
      <button onClick={sendCode} className="text-sm underline w-full">Resend code</button>
    </div>)}
    {step === 'done' && (<div className="space-y-3 text-center">
      <p className="font-bold">You're signed in 🎉</p>
      <a href="/" className="inline-block bg-[#0E7C5B] text-white rounded-lg px-4 py-3 font-bold">Continue to Dashboard →</a>
      <div><button onClick={out} className="text-sm underline text-gray-600">Sign out</button></div>
    </div>)}
  </div>);
}
