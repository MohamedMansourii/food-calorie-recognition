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
    <aside className="rounded-2xl bg-white p-4 shadow-sm">
      <h2 className="mb-3 font-semibold text-slate-700">This session</h2>
      {entries.length === 0 ? (
        <p className="text-sm text-slate-400">Analyzed meals will appear here. History clears when you close the tab.</p>
      ) : (
        <ul className="space-y-3">
          {entries.map((e) => (
            <li key={e.id} className="flex items-center gap-3">
              <img src={e.thumbUrl} alt="" className="h-12 w-12 rounded-lg object-cover" />
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-slate-700">{e.displayName}</p>
                <p className="text-xs text-slate-500">
                  ~{e.kcal} kcal · {e.portionG} g · {e.time}
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
}
