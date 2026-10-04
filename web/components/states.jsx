export function Loading({ n = 3 }) { return (<div className="space-y-2">{Array.from({ length: n }).map((_, i) => (<div key={i} className="h-4 bg-gray-200 rounded animate-pulse" />))}</div>); }
export function Empty({ text, cta, href }) { return (<div className="border rounded-xl p-6 text-center bg-white"><p className="text-4xl">📭</p><p className="mt-2 text-sm">{text}</p><a className="underline font-bold text-sm" href={href}>{cta}</a></div>); }
export function ErrorBox({ onRetry }) { return (<div className="border rounded-xl p-6 text-center bg-white"><p className="text-4xl">⚠️</p><p className="text-sm mt-2">Something failed.</p><button onClick={onRetry} className="underline font-bold text-sm mt-1">Retry</button></div>); }
export function OfflineBar() { return (<div className="bg-yellow-100 border rounded-lg p-2 text-xs mb-3">📴 Offline — showing cached lesson. Attempts will queue & sync.</div>); }
export function LangToggle({ lang, setLang }) {
  return (<div className="flex gap-2 flex-wrap">{['en', 'pcm', 'yo', 'ha', 'ig'].map(l => (<button key={l} onClick={() => setLang(l)} className={`border rounded-full px-3 py-1 text-xs ${lang === l ? 'bg-black text-white' : 'bg-white'}`}>{l.toUpperCase()}</button>))}</div>);
}
export function DataSaver({ on, setOn }) { return (<button onClick={() => setOn(!on)} className="text-xs font-bold border rounded-full px-3 py-1 bg-white">{on ? '● Data Saver ON' : '○ Data Saver OFF'}</button>); }
