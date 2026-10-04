import './globals.css';
export const metadata = { title: 'Education AI Tutor', description: 'Learn better. Practice smarter.' };
export default function RootLayout({ children }) {
  return (<html lang="en"><body className="bg-[#F6F8F7] text-[#14211C]">
    <div className="max-w-6xl mx-auto px-4 md:px-8">
      <header className="py-4 flex justify-between items-center">
        <b>🎓 AI Tutor</b>
        <nav className="flex gap-2 text-sm"><a href="/">Learn</a><a href="/practice">Practice</a><a href="/exam">Exam</a><a href="/revision">Revise</a><a href="/onboarding">Setup</a></nav>
      </header>
      <main className="pb-20 md:pb-10">{children}</main>
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t flex justify-around py-3 text-xs md:hidden">
        <a href="/">Learn</a><a href="/practice">Practice</a><a href="/exam">Exam</a><a href="/ask">Ask</a><a href="/revision">Revise</a>
      </nav>
    </div></body></html>);
}
