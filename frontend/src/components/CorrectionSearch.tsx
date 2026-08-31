// "Wrong food?" manual correction (FR-05): debounced search over names + aliases.
import { useEffect, useRef, useState } from "react";
import { searchFoods, type FoodSearchHit } from "../api";

interface Props {
  onSelect: (hit: FoodSearchHit) => void;
  onClose: () => void;
}

export default function CorrectionSearch({ onSelect, onClose }: Props) {
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<FoodSearchHit[]>([]);
  const [searching, setSearching] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => inputRef.current?.focus(), []);

  useEffect(() => {
    if (query.trim().length < 2) {
      setHits([]);
      return;
    }
    setSearching(true);
    const t = setTimeout(() => {
      searchFoods(query)
        .then(setHits)
        .catch(() => setHits([]))
        .finally(() => setSearching(false));
    }, 250); // debounce
    return () => clearTimeout(t);
  }, [query]);

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
      <div className="flex items-center gap-2">
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search a food (e.g. couscous, ojja, burger)…"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          aria-label="Search for the correct food"
        />
        <button onClick={onClose} className="text-sm text-slate-500 hover:text-slate-700">
          Cancel
        </button>
      </div>
      {searching && <p className="mt-2 text-xs text-slate-400">Searching…</p>}
      {!searching && query.trim().length >= 2 && hits.length === 0 && (
        <p className="mt-2 text-xs text-slate-400">No matches in the 101 known foods.</p>
      )}
      {hits.length > 0 && (
        <ul className="mt-2 max-h-56 divide-y divide-slate-100 overflow-y-auto">
          {hits.map((hit) => (
            <li key={hit.label}>
              <button
                onClick={() => onSelect(hit)}
                className="w-full px-2 py-2 text-left text-sm hover:bg-emerald-50"
              >
                {hit.display_name}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
