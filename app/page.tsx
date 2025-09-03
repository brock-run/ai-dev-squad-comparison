export default function LandingPage() {
    return (
        <div className="space-y-6">
            <div className="space-y-2">
                <h1 className="text-3xl md:text-4xl font-bold tracking-tight">🏔️ Memory Flip Battle</h1>
                <p className="opacity-80 max-w-prose">
                    A cozy two‑player online memory game with a mountain vibe. Match pairs on your turn to earn a
                    <b> Truth</b> or <b> Dare</b> prompt for your partner. Play a single round or a <b>best‑of series</b> (3/5/7).
                </p>
            </div>

            <div className="grid md:grid-cols-2 gap-4">
                <div className="rounded-2xl bg-white/5 border border-white/10 p-4 space-y-2">
                    <h2 className="text-lg font-semibold">How to play</h2>
                    <ol className="list-decimal list-inside opacity-90 space-y-1 text-sm">
                        <li>Open <code>/play</code>. One player clicks <b>Create</b> to generate a room code.</li>
                        <li>Share the code. Your partner enters it and clicks <b>Join</b>.</li>
                        <li>Choose <b>Pairs</b> and <b>Best of</b>, then click <b>Start Game</b>.</li>
                        <li>On your turn, flip two cards. A match keeps your turn and opens the Truth/Dare composer.</li>
                        <li>Series winner is declared automatically.</li>
                    </ol>
                </div>

                <div className="rounded-2xl bg-white/5 border border-white/10 p-4 space-y-2">
                    <h2 className="text-lg font-semibold">One‑time setup</h2>
                    <ul className="list-disc list-inside opacity-90 space-y-1 text-sm">
                        <li>Create a Firebase project → Web App → copy the config.</li>
                        <li>Set the <code>NEXT_PUBLIC_FIREBASE_*</code> env vars on Vercel <i>or</i> paste JSON at runtime on <code>/play</code>.</li>
                        <li><code>npm i firebase framer-motion uuid</code></li>
                    </ul>
                    <div className="pt-2">
                        <a href="/play" className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700">
                            Start playing →
                        </a>
                    </div>
                </div>
            </div>

            <div className="rounded-2xl bg-white/5 border border-white/10 p-4 text-xs opacity-70">
                Privacy tip: rooms are ephemeral and identified by a random code. For private games, avoid sharing the URL/code publicly.
            </div>
        </div>
    );
}
