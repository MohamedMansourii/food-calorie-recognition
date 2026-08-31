// In-session history (FR-09) — memory only, gone on refresh, no accounts.
export interface HistoryEntry {
  id: number;
  thumbUrl: string;
  displayName: string;
  kcal: number;
  portionG: number;
  time: string;
}

interface Props {
  entries: HistoryEntry[];
}

export default function HistorySidebar({ entries }: Props) {
  return (
    <aside className="h-fit rounded-3xl bg-white/90 p-4 shadow-lg shadow-slate-900/5 ring-1 ring-slate-100">
      <h2 className="mb-3 flex items-center gap-2 font-semibold text-slate-700">
        <span className="text-base">🕘</span> This session
      </h2>
      {entries.length === 0 ? (
        <p className="text-sm leading-relaxed text-slate-400">
          Analyzed meals will appear here. History clears when you close the tab — nothing is stored.
        </p>
      ) : (
        <ul className="space-y-2">
          {entries.map((e) => (
            <li key={e.id} className="flex items-center gap-3 rounded-2xl p-2 transition-colors hover:bg-slate-50">
              <img src={e.thumbUrl} alt="" className="h-12 w-12 rounded-xl object-cover shadow-sm" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-slate-700">{e.displayName}</p>
                <p className="text-xs text-slate-400">{e.portionG} g · {e.time}</p>
              </div>
              <span className="shrink-0 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-bold text-emerald-700">
                {e.kcal}
              </span>
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
}
