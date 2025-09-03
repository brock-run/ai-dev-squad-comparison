import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = { title: 'Memory Flip Battle — Mountain Edition' };

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="en">
        <body className="min-h-screen bg-slate-950 text-slate-100">
        <header className="border-b border-white/10">
            <div className="max-w-5xl mx-auto p-4 flex items-center justify-between">
                <a href="/" className="text-lg font-semibold flex items-center gap-2">
                    <span>🏔️</span>
                    <span>Memory Flip Battle</span>
                </a>
                <nav className="text-sm">
                    <a href="/play" className="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700">Play</a>
                </nav>
            </div>
        </header>
        <main className="max-w-5xl mx-auto p-4 md:p-8">{children}</main>
      </body>
    </html>
  );
}