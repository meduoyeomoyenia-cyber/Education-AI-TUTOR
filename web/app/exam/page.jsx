'use client';
import { useState } from 'react';
export default function Exam() {
  const [t] = useState('01:24:36');
  return (<div className="bg-white border rounded-xl p-5 max-w-xl"><h1 className="font-extrabold">JAMB Mock</h1><p className="text-sm font-bold text-orange-600">⏱ {t} remaining • auto-submit on time</p><p className="text-sm mt-2">Timed exam uses same QuestionCard + MockTimer. Untimed mode available.</p></div>);
}
