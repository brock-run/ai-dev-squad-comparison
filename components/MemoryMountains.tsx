'use client';

import React, { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { v4 as uuidv4 } from "uuid";

/**
 * Game component used at /play
 * Includes: Firebase sync, turn-based memory, Truth/Dare feed, and Best-of series (3/5/7)
 */

// --- Firebase (lazy init) ---
import { initializeApp, getApps } from "firebase/app";
import {
  getFirestore,
  doc,
  setDoc,
  updateDoc,
  onSnapshot,
  serverTimestamp,
  runTransaction,
} from "firebase/firestore";

const envConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY || "",
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || "",
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || "",
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET || "",
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID || "",
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID || "",
};

let _db: ReturnType<typeof getFirestore> | null = null as any;
function ensureDb(config?: any) {
  const cfg = config || envConfig;
  if (!cfg || !cfg.apiKey) return null;
  if (!getApps().length) initializeApp(cfg);
  _db = getFirestore();
  return _db;
}

// --- Game constants ---
const MOUNTAIN_SET = [
  "⛰️", // mountain
  "⛺️", // tent
  "🚧", // construction (trail sign alt)
  "🌄", // sunrise over mountains
  "⛄️", // snowman
  "🌳", // evergreen
  "🐻", // bear
  "❄️", // snowflake
  "🚶‍♂️", // hiker (person walking)
  "🌋", // volcano
];

const DEFAULT_PAIRS = 8; // 16 cards
const DEFAULT_BEST_OF = 3;

const DEFAULT_TRUTH = [
  "What’s a fear you’ve faced that made you proud?",
  "When did you feel most supported by me recently?",
  "What’s a small habit you’d love to start this week?",
  "What’s a favorite trip memory we share?",
  "What’s something new you want us to try together?",
  "What’s a hill (or mountain) you’d die on?",
  "What’s a secret talent I might not know about?",
  "When have I made you laugh the hardest lately?",
];

const DEFAULT_DARE = [
  "Send a 10-second voice note doing your best mountain yodel.",
  "Share a photo from your camera roll that feels ‘cozy cabin’.",
  "Text me a spontaneous mini-poem (4 lines) about tonight.",
  "Do 10 jumping jacks on camera—trail warmup!",
  "Speak only in emojis for the next round.",
  "Swap your Zoom/Meet background to a mountain pic.",
  "Set a 24-hour reminder to plan a micro-adventure together.",
  "Give me one sincere compliment with a hiking metaphor.",
];

// --- Helpers ---
function makeDeck(pairCount = DEFAULT_PAIRS) {
  const picks = shuffle(MOUNTAIN_SET).slice(0, pairCount);
  const deck = shuffle(
    picks.flatMap((val) => [
      { id: uuidv4(), value: val, matchedBy: null },
      { id: uuidv4(), value: val, matchedBy: null },
    ])
  );
  return deck as { id: string; value: string; matchedBy: string | null }[];
}

function shuffle<T>(arr: T[]): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function sleep(ms: number) { return new Promise((res) => setTimeout(res, ms)); }

function chooseRandomPlayerId(players: Record<string, any>) {
  const ids = Object.keys(players || {});
  return ids[Math.floor(Math.random() * ids.length)] || null;
}

function nextPlayerId(players: Record<string, any>, currentId: string) {
  const ids = Object.keys(players || {});
  if (ids.length <= 1) return currentId;
  const idx = ids.indexOf(currentId);
  return ids[(idx + 1) % ids.length];
}

function generateRoomCode() {
  const words = ["ROCKY","RIDGE","ALPINE","LODGE","PEAKS","SUMMIT","GLACIER","CABIN","CANYON","BROOK","CEDAR","QUARTZ"];
  const w = words[Math.floor(Math.random()*words.length)];
  const num = String(Math.floor(100 + Math.random()*900));
  return `${w}-${num}`;
}

export default function MemoryMountains() {
  const [playerName, setPlayerName] = useState("");
  const [playerId] = useState(() => uuidv4());
  const [roomCode, setRoomCode] = useState("");
  const [joining, setJoining] = useState(false);
  const [room, setRoom] = useState<any>(null);
  const [me, setMe] = useState<any>(null);

  // Firebase config fallback UI if env not set
  const [needsConfig, setNeedsConfig] = useState(!envConfig.apiKey);
  const [configInput, setConfigInput] = useState("
{
  \"apiKey\": \"...\",
  \"authDomain\": \"...\",
  \"projectId\": \"...\",
  \"storageBucket\": \"...\",
  \"messagingSenderId\": \"...\",
  \"appId\": \"...\"
}
");

  useEffect(() => {
    if (_db) return;
    if (envConfig.apiKey) {
      ensureDb(envConfig);
      setNeedsConfig(false);
    } else if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('firebaseConfig');
      if (saved) {
        try { const parsed = JSON.parse(saved); if (parsed.apiKey) { ensureDb(parsed); setNeedsConfig(false); } } catch {}
      }
    }
  }, []);

  const saveRuntimeConfig = () => {
    try {
      const parsed = JSON.parse(configInput);
      if (!parsed.apiKey) throw new Error('Missing apiKey');
      localStorage.setItem('firebaseConfig', JSON.stringify(parsed));
      ensureDb(parsed);
      setNeedsConfig(false);
    } catch (e: any) {
      alert(`Invalid JSON: ${e.message}`);
    }
  };

  const roomRef = useMemo(() => (_db && roomCode ? doc(_db, "rooms", roomCode) : null), [roomCode]);

  // Subscribe to room
  useEffect(() => {
    if (!_db || !roomRef) return;
    const unsub = onSnapshot(roomRef, (snap) => {
      setRoom(snap.exists() ? snap.data() : null);
    });
    return () => unsub();
  }, [roomRef]);

  useEffect(() => {
    if (!room) return;
    setMe(room.players?.[playerId] ?? null);
  }, [room, playerId]);

  const inRoom = !!room && !!me;

  // Create room
  const handleCreate = async () => {
    if (!_db) return alert("Firebase not configured yet");
    if (!playerName.trim()) return alert("Enter your name");
    const code = generateRoomCode();
    setRoomCode(code);
    const deck = makeDeck();
    await setDoc(doc(_db, "rooms", code), {
      createdAt: serverTimestamp(),
      deck,
      faceUp: [],
      matchedIds: [],
      turn: playerId,
      players: {
        [playerId]: { id: playerId, name: playerName, score: 0, joinedAt: Date.now() },
      },
      started: false,
      finished: false,
      feed: [],
      bank: { truth: DEFAULT_TRUTH, dare: DEFAULT_DARE },
      settings: { pairs: DEFAULT_PAIRS, seriesBestOf: DEFAULT_BEST_OF },
      series: {
        bestOf: DEFAULT_BEST_OF,
        wins: { [playerId]: 0 },
        completed: false,
        championId: null,
        round: 0,
        roundWinRecorded: false,
      },
    });
  };

  // Join room
  const handleJoin = async () => {
    if (!_db) return alert("Firebase not configured yet");
    if (!playerName.trim() || !roomCode.trim()) return alert("Enter your name and room code");
    setJoining(true);
    try {
      await runTransaction(_db, async (tx) => {
        const ref = doc(_db!, "rooms", roomCode);
        const snap = await tx.get(ref);
        if (!snap.exists()) throw new Error("Room not found");
        const data: any = snap.data();
        const players = data.players || {};
        players[playerId] = { id: playerId, name: playerName, score: 0, joinedAt: Date.now() };
        const series = data.series || { bestOf: DEFAULT_BEST_OF, wins: {}, completed: false, championId: null, round: 0, roundWinRecorded: false };
        if (!(playerId in (series.wins || {}))) {
          series.wins = { ...(series.wins || {}), [playerId]: 0 };
        }
        tx.update(ref, { players, series });
      });
    } catch (e: any) {
      alert(e.message);
    } finally {
      setJoining(false);
    }
  };

  // Start round
  const handleStart = async () => {
    if (!_db || !roomRef) return;
    const deck = makeDeck(room?.settings?.pairs || DEFAULT_PAIRS);
    const nextTurn = chooseRandomPlayerId(room.players);
    const nextRound = (room.series?.round || 0) + 1;
    await updateDoc(roomRef, {
      deck,
      faceUp: [],
      matchedIds: [],
      turn: nextTurn,
      started: true,
      finished: false,
      feed: [],
      series: { ...(room.series || {}), round: nextRound, roundWinRecorded: false },
    });
  };

  // Reset series
  const handleResetSeries = async () => {
    if (!_db || !roomRef) return;
    const blankWins: Record<string, number> = {};
    Object.keys(room.players || {}).forEach((id) => { blankWins[id] = 0; });
    await updateDoc(roomRef, {
      series: {
        bestOf: room?.settings?.seriesBestOf || DEFAULT_BEST_OF,
        wins: blankWins,
        completed: false,
        championId: null,
        round: 0,
        roundWinRecorded: false,
      },
      started: false,
      finished: false,
    });
  };

  // Card click
  const onCardClick = async (cardId: string) => {
    if (!_db || !roomRef || !room?.started || room.finished) return;
    if (room.turn !== playerId) return;
    if (room.faceUp.includes(cardId)) return;
    if (room.matchedIds.includes(cardId)) return;

    await runTransaction(_db, async (tx) => {
      const snap = await tx.get(roomRef);
      const data: any = snap.data();
      if (!data || data.turn !== playerId) return;

      const faceUp: string[] = [...data.faceUp];
      if (faceUp.length === 2) return;
      faceUp.push(cardId);

      if (faceUp.length === 2) {
        const [a, b] = faceUp.map((id) => data.deck.find((c: any) => c.id === id));
        if (a && b && a.value === b.value) {
          const matchedIds = [...data.matchedIds, a.id, b.id];
          const players = { ...data.players };
          players[playerId].score = (players[playerId].score || 0) + 1;
          tx.update(roomRef, { faceUp: [], matchedIds, players });
        } else {
          tx.update(roomRef, { faceUp });
        }
      } else {
        tx.update(roomRef, { faceUp });
      }
    });
  };

  // After two up and not a match → flip back + pass; detect end of round
  useEffect(() => {
    const manage = async () => {
      if (!_db || !roomRef || !room) return;
      const faceUp = room.faceUp || [];
      if (faceUp.length === 2) {
        const [a, b] = faceUp.map((id: string) => room.deck.find((c: any) => c.id === id));
        if (!a || !b) return;
        if (a.value !== b.value) {
          await sleep(900);
          const next = nextPlayerId(room.players, room.turn);
          await updateDoc(roomRef, { faceUp: [], turn: next });
        }
      }

      const allMatched = room.matchedIds?.length === room.deck?.length;
      if (room.started && allMatched && !room.finished) {
        await updateDoc(roomRef, { finished: true });
      }
    };
    manage();
  }, [room?.faceUp, room?.matchedIds, room?.started]);

  // Round result → increment best-of wins once
  const prevFinishedRef = useRef(false);
  useEffect(() => {
    const settleRound = async () => {
      if (!_db || !roomRef || !room) return;
      if (!room.finished || room.series?.roundWinRecorded) return;

      const playersArr = Object.values(room.players || {}) as any[];
      const topScore = Math.max(...playersArr.map((p) => p.score || 0));
      const winners = playersArr.filter((p) => (p.score || 0) === topScore);

      await runTransaction(_db, async (tx) => {
        const snap = await tx.get(roomRef);
        if (!snap.exists()) return;
        const data: any = snap.data();
        if (!data.finished || data.series?.roundWinRecorded) return;

        const series = { ...(data.series || {}) };
        series.roundWinRecorded = true;

        if (winners.length === 1) {
          const winnerId = winners[0].id;
          series.wins = { ...(series.wins || {}) };
          series.wins[winnerId] = (series.wins[winnerId] || 0) + 1;
          const target = Math.floor((series.bestOf || DEFAULT_BEST_OF) / 2) + 1;
          if (series.wins[winnerId] >= target) {
            series.completed = true;
            series.championId = winnerId;
          }
        }
        tx.update(roomRef, { series });
      });
    };
    if (room?.finished && !prevFinishedRef.current) settleRound();
    prevFinishedRef.current = !!room?.finished;
  }, [room?.finished]);

  // Prompt composer trigger
  const [showPromptComposer, setShowPromptComposer] = useState(false);
  const [promptType, setPromptType] = useState<"truth" | "dare">("truth");
  const [customPrompt, setCustomPrompt] = useState("");
  const prevScoreRef = useRef(0);
  useEffect(() => {
    if (!room || !me) return;
    const now = me.score || 0;
    if (now > prevScoreRef.current) setShowPromptComposer(true);
    prevScoreRef.current = now;
  }, [room?.players, me?.score]);

  const askPrompt = async () => {
    if (!_db || !roomRef) return;
    const bank = room.bank || { truth: [], dare: [] };
    let text = customPrompt.trim();
    if (!text) {
      const pool = (promptType === "truth" ? bank.truth : bank.dare) || [];
      text = pool[Math.floor(Math.random() * pool.length)] || "Your choice!";
    }
    const targetId = Object.keys(room.players).find((id) => id !== playerId) || playerId;
    const entry = { id: uuidv4(), ts: Date.now(), from: playerId, to: targetId, type: promptType, text };
    const feed = [...(room.feed || []), entry];
    await updateDoc(roomRef, { feed });
    setCustomPrompt("");
    setShowPromptComposer(false);
  };

  const addBankItem = async (kind: "truth" | "dare", value: string) => {
    if (!_db || !roomRef) return;
    const clean = value.trim();
    if (!clean) return;
    const bank = room.bank || { truth: [], dare: [] };
    const updated = { ...bank, [kind]: [...(bank[kind] || []), clean] };
    await updateDoc(roomRef, { bank: updated });
  };

  // --- Entry vs In-room views ---
  const entryView = (
    <div className="rounded-2xl bg-white/5 border border-white/10 overflow-hidden">
      <div className="p-4 border-b border-white/10 flex items-center justify-between">
        <div className="text-lg font-semibold">Play Together (Online)</div>
        {!!room && (
          <div className="text-sm opacity-80">Room: <span className="font-mono tracking-wider">{roomCode}</span></div>
        )}
      </div>
      <div className="p-4 grid md:grid-cols-3 gap-4">
        <div className="md:col-span-1 space-y-2">
          <label className="text-sm">Your name</label>
          <input className="w-full px-3 py-2 rounded-xl bg-white/10 border border-white/10" placeholder="e.g., Lynn or Alex" value={playerName} onChange={(e) => setPlayerName(e.target.value)} />
        </div>
        <div className="md:col-span-1 space-y-2">
          <label className="text-sm">Room code</label>
          <input className="w-full px-3 py-2 rounded-xl bg-white/10 border border-white/10" placeholder="e.g., ROCKY-123" value={roomCode} onChange={(e) => setRoomCode(e.target.value.toUpperCase())} />
        </div>
        <div className="md:col-span-1 flex items-end gap-2">
          <button className="w-full px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700" onClick={handleCreate}>Create</button>
          <button className="w-full px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20" onClick={handleJoin} disabled={joining}>Join</button>
        </div>
        <div className="md:col-span-3 text-xs opacity-70">
          Tip: One person clicks <b>Create</b> (a new code appears). The other enters that code and clicks <b>Join</b>.
        </div>
      </div>
    </div>
  );

  const inRoomView = (
    <div className="grid lg:grid-cols-3 gap-4">
      {/* Game board */}
      <div className="lg:col-span-2 bg-white/5 border border-white/10 rounded-2xl relative overflow-hidden">
        {/* Subtle mountain silhouette */}
        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-32 opacity-20">
          <svg viewBox="0 0 1440 320" className="absolute bottom-0 w-full">
            <path fill="currentColor" d="M0,256L80,213.3C160,171,320,85,480,85.3C640,85,800,171,960,176C1120,181,1280,107,1360,69.3L1440,32L1440,320L1360,320C1280,320,1120,320,960,320C800,320,640,320,480,320C320,320,160,320,80,320L0,320Z" />
          </svg>
        </div>

        <div className="p-4 border-b border-white/10 flex flex-col gap-2 relative z-10">
          <div className="flex justify-between items-center">
            <div className="text-lg font-semibold">Board</div>
            <div className="flex items-center gap-2 text-sm">
              {room?.started ? (
                <>
                  <span>Turn:</span>
                  <span className={`px-2 py-1 rounded-xl font-medium ${room.turn === playerId ? "bg-emerald-500/20 text-emerald-200" : "bg-white/10"}`}>
                    {room.players[room.turn]?.name || "?"}
                  </span>
                </>
              ) : (
                <span className="opacity-80">Waiting to start…</span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-3 text-sm opacity-80 flex-wrap">
            <span>Players:</span>
            <div className="flex gap-2 flex-wrap">
              {Object.values(room.players).map((p: any) => (
                <span key={p.id} className="px-2 py-1 rounded-xl bg-white/10">{p.name}</span>
              ))}
            </div>
          </div>
          {!room.started && (
            <div className="flex items-center gap-3 flex-wrap">
              <div className="flex items-center gap-2">
                <label htmlFor="pairs" className="text-sm">Pairs</label>
                <input
                  id="pairs"
                  type="number"
                  min={4}
                  max={10}
                  value={room?.settings?.pairs || DEFAULT_PAIRS}
                  onChange={async (e) => {
                    const val = Math.max(4, Math.min(10, Number(e.target.value)));
                    roomRef && await updateDoc(roomRef, { settings: { ...(room.settings||{}), pairs: val } });
                  }}
                  className="w-24 px-3 py-2 rounded-xl bg-white/10 border border-white/10"
                />
              </div>
              <div className="flex items-center gap-2">
                <label className="text-sm">Best of</label>
                <select
                  className="px-3 py-2 rounded-xl bg-white/10 border border-white/10"
                  value={room?.settings?.seriesBestOf || DEFAULT_BEST_OF}
                  onChange={async (e) => {
                    const val = Number(e.target.value);
                    if (!roomRef) return;
                    await updateDoc(roomRef, {
                      settings: { ...(room.settings||{}), seriesBestOf: val },
                      series: { ...(room.series||{}), bestOf: val },
                    });
                  }}
                >
                  {[3,5,7].map(n => <option key={n} value={n}>Best of {n}</option>)}
                </select>
              </div>
              <button className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700" onClick={handleStart}>Start Game</button>
            </div>
          )}
        </div>

        <div className="p-4 relative z-10">
          {room.started ? (
            <Board room={room} meId={playerId} onCardClick={onCardClick} />
          ) : (
            <div className="text-xs opacity-80">Theme: mountains 🏔️ • flip to match pairs • match grants a Truth/Dare</div>
          )}
        </div>
      </div>

      {/* Sidebar */}
      <div className="space-y-4">
        <div className="bg-white/5 border border-white/10 rounded-2xl">
          <div className="p-4 border-b border-white/10 flex items-center justify-between">
            <div className="text-lg font-semibold">Score</div>
            <div className="text-xs opacity-70">Best of {room?.series?.bestOf || DEFAULT_BEST_OF}</div>
          </div>
          <div className="p-4 flex gap-2 flex-wrap items-center">
            {Object.values(room.players)
              .sort((a: any,b: any) => (b.score||0) - (a.score||0))
              .map((p: any) => (
                <div key={p.id} className={`px-3 py-2 rounded-2xl shadow ${p.id === playerId ? "bg-emerald-500/20 text-emerald-100" : "bg-white/10"}`}>
                  <span className="font-semibold">{p.name}</span>: {p.score}
                </div>
              ))}

            <div className="w-full mt-2 text-sm">
              <div className="opacity-80 mb-1">Series wins</div>
              <div className="flex gap-2 flex-wrap">
                {Object.values(room.players).map((p: any) => (
                  <span key={p.id} className="px-2 py-1 rounded-xl bg-white/10">
                    {p.name}: {room.series?.wins?.[p.id] ?? 0}
                  </span>
                ))}
              </div>
            </div>

            {room.finished && (
              <div className="w-full mt-2 text-sm flex items-center gap-2">
                <span className="px-2 py-1 rounded bg-white/10">Round complete{room.series?.completed ? ' • Series finished' : ''}!</span>
                {!room.series?.completed && (
                  <button className="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700" onClick={handleStart}>Next Round</button>
                )}
                <button className="px-3 py-1.5 rounded-xl bg-white/10 hover:bg-white/20" onClick={handleResetSeries}>Reset Series</button>
              </div>
            )}

            {room.series?.completed && (
              <div className="w-full mt-2 p-3 rounded-xl bg-emerald-500/15 border border-emerald-500/30">
                <div className="text-sm">
                  🏆 Series winner: <b>{room.players[room.series.championId]?.name || '—'}</b>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="bg-white/5 border border-white/10 rounded-2xl">
          <div className="p-4 border-b border-white/10">
            <div className="text-lg font-semibold">Truth / Dare</div>
          </div>
          <div className="p-4 space-y-3">
            <div className="text-sm opacity-80">Match a pair on your turn to ask your partner a prompt.</div>

            <AnimatePresence>
              {showPromptComposer && (
                <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }}>
                  <div className="p-3 rounded-xl bg-emerald-500/15 border border-emerald-500/30 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">You matched! Ask a prompt</span>
                      <div className="flex items-center gap-2 text-xs">
                        <label className="opacity-80">Truth</label>
                        <input type="checkbox" checked={promptType === 'dare'} onChange={(e) => setPromptType(e.target.checked ? 'dare' : 'truth')} />
                        <label className="opacity-80">Dare</label>
                      </div>
                    </div>
                    <textarea
                      className="w-full min-h-[90px] p-2 rounded-lg bg-white/10 border border-white/10"
                      placeholder={`Type a ${promptType} or leave blank to draw from the bank…`}
                      value={customPrompt}
                      onChange={(e) => setCustomPrompt(e.target.value)}
                    />
                    <div className="flex gap-2">
                      <button className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700" onClick={askPrompt}>Ask</button>
                      <button className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20" onClick={() => setShowPromptComposer(false)}>Dismiss</button>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Add to bank */}
            <div className="space-y-2">
              <div className="text-xs opacity-80">Add to prompt bank</div>
              <div className="flex gap-2">
                <input className="flex-1 px-3 py-2 rounded-xl bg-white/10 border border-white/10" placeholder="Add a Truth… (press Enter)" onKeyDown={async (e: any) => {
                  if (e.key === 'Enter') { await addBankItem('truth', e.currentTarget.value); e.currentTarget.value=''; }
                }} />
                <input className="flex-1 px-3 py-2 rounded-xl bg-white/10 border border-white/10" placeholder="Add a Dare… (press Enter)" onKeyDown={async (e: any) => {
                  if (e.key === 'Enter') { await addBankItem('dare', e.currentTarget.value); e.currentTarget.value=''; }
                }} />
              </div>
            </div>

            {/* Feed */}
            <div className="space-y-2 max-h-72 overflow-auto pr-2">
              {[...(room.feed||[])].sort((a: any,b: any)=>a.ts-b.ts).map((f: any) => (
                <div key={f.id} className="p-3 rounded-xl bg-white/5 border border-white/10">
                  <div className="text-xs opacity-70 mb-1">
                    {room.players[f.from]?.name} → {room.players[f.to]?.name} • {f.type}
                  </div>
                  <div className="text-sm">{f.text}</div>
                </div>
              ))}
              {(!room.feed || room.feed.length===0) && (
                <div className="text-xs opacity-60">No prompts yet. Match a pair to ask one!</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-4">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight flex items-center gap-3">
          <span>🏔️ Memory Flip Battle</span>
          <span className="text-sm md:text-base font-normal opacity-80">Mountain Edition</span>
        </h1>
        {inRoom && (
          <div className="text-sm opacity-80">Room: <span className="font-mono tracking-wider">{roomCode}</span></div>
        )}
      </header>

      {inRoom ? inRoomView : entryView}

      <footer className="pt-2 text-xs opacity-70">
        <div>Tip: If cards don’t flip for both of you, confirm both are using the same room code and that Firestore is enabled.</div>
      </footer>

      {needsConfig && (
        <div className="min-h-[50vh] w-full bg-slate-950 text-slate-100 p-6 rounded-2xl border border-white/10 mt-4">
          <h2 className="text-xl font-semibold mb-2">Firebase config</h2>
          <p className="opacity-80 max-w-prose">Set NEXT_PUBLIC_* env vars on Vercel, or paste your Firebase web config JSON below (saved in this browser only):</p>
          <textarea className="mt-4 w-full h-56 p-3 rounded-lg bg-slate-900 border border-white/10 font-mono text-sm" value={configInput} onChange={(e) => setConfigInput(e.target.value)} />
          <div className="mt-3 flex gap-2">
            <button className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700" onClick={saveRuntimeConfig}>Save config</button>
          </div>
        </div>
      )}
    </div>
  );
}

function Board({ room, meId, onCardClick }: { room: any; meId: string; onCardClick: (id: string) => void }) {
  const gridCols = room.deck.length <= 16 ? "grid-cols-4" : "grid-cols-5";
  return (
    <div className={`grid ${gridCols} gap-3 place-items-stretch`}>
      {room.deck.map((card: any) => {
        const isFaceUp = room.faceUp.includes(card.id) || room.matchedIds.includes(card.id);
        const isMatched = room.matchedIds.includes(card.id);
        return (
          <FlipCard key={card.id} faceUp={isFaceUp} matched={isMatched} onClick={() => onCardClick(card.id)}>
            <span className="text-4xl md:text-5xl">{card.value}</span>
          </FlipCard>
        );
      })}
    </div>
  );
}

function FlipCard({ children, faceUp, matched, onClick }: any) {
  return (
    <motion.button
      onClick={onClick}
      className={`relative aspect-square rounded-2xl w-full shadow-inner focus:outline-none focus:ring-2 focus:ring-emerald-400/60 ${matched ? "opacity-70" : ""}`}
      whileTap={{ scale: 0.98 }}
      disabled={matched}
    >
      <motion.div
        className="absolute inset-0"
        style={{ transformStyle: 'preserve-3d' as any }}
        animate={{ rotateY: faceUp ? 180 : 0 }}
        transition={{ duration: 0.45 }}
      >
        {/* Back */}
        <div
          className="absolute inset-0 rounded-2xl bg-gradient-to-br from-sky-600/30 to-indigo-700/30 border border-white/10 flex items-center justify-center"
          style={{ backfaceVisibility: 'hidden' as any }}
        >
          <div className="flex flex-col items-center gap-1">
            <span className="text-3xl">🏔️</span>
            <span className="text-[10px] uppercase tracking-widest opacity-80">Flip</span>
          </div>
        </div>
        {/* Front */}
        <div
          className="absolute inset-0 rounded-2xl bg-white/90 text-slate-900 flex items-center justify-center"
          style={{ backfaceVisibility: 'hidden' as any, transform: 'rotateY(180deg)' }}
        >
          {children}
        </div>
      </motion.div>
    </motion.button>
  );
}
