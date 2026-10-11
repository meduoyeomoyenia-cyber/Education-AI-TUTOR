'use client';
import { useEffect, useState } from 'react';

export function SwRegister() {
  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(() => {});
    }
  }, []);
  return null;
}

export function InstallButton() {
  const [deferred, setDeferred] = useState(null);
  const [installed, setInstalled] = useState(false);
  const [ios, setIos] = useState(false);
  useEffect(() => {
    setInstalled(window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true);
    setIos(/iphone|ipad|ipod/i.test(window.navigator.userAgent) && !window.MSStream);
    const onPrompt = (e) => { e.preventDefault(); setDeferred(e); };
    const onInstalled = () => { setInstalled(true); setDeferred(null); };
    window.addEventListener('beforeinstallprompt', onPrompt);
    window.addEventListener('appinstalled', onInstalled);
    return () => { window.removeEventListener('beforeinstallprompt', onPrompt); window.removeEventListener('appinstalled', onInstalled); };
  }, []);
  if (installed) return null;
  if (deferred) {
    return (<button onClick={() => { deferred.prompt(); deferred.userChoice.then(() => setDeferred(null)); }}
      className="bg-[#0E7C5B] text-white rounded-full px-4 py-2 text-sm font-bold">⬇ Install App</button>);
  }
  if (ios) {
    return (<span className="text-xs border rounded-full px-3 py-1 bg-white" title="Tap Share, then Add to Home Screen">📲 Share → Add to Home Screen to install</span>);
  }
  return null;
}
