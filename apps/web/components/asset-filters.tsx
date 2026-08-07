'use client';

interface Props {
  type: string;
  setType: (v: string) => void;
  tag: string;
  setTag: (v: string) => void;
  sort: string;
  setSort: (v: string) => void;
}

export function AssetFilters({ type, setType, tag, setTag, sort, setSort }: Props) {
  return (
    <div className="flex gap-3 flex-wrap">
      <select value={type} onChange={e => setType(e.target.value)}
        className="h-9 px-3 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-white text-xs">
        <option value="">All Types</option>
        <option value="image">Image</option>
        <option value="video">Video</option>
        <option value="audio">Audio</option>
      </select>
      <input type="text" value={tag} onChange={e => setTag(e.target.value)} placeholder="Filter by tag..."
        className="h-9 px-3 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-white text-xs w-40" />
      <select value={sort} onChange={e => setSort(e.target.value)}
        className="h-9 px-3 rounded-lg bg-white/[0.04] border border-[var(--glass-border)] text-white text-xs">
        <option value="created_desc">Newest</option>
        <option value="created_asc">Oldest</option>
        <option value="name_asc">Name A-Z</option>
        <option value="size_desc">Largest</option>
      </select>
    </div>
  );
}
