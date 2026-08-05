'use client';

interface Props {
  confidence: string;
  setConfidence: (v: string) => void;
  search: string;
  setSearch: (v: string) => void;
  sortBy: string;
  setSortBy: (v: string) => void;
}

export function IdeaFilters({
  confidence,
  setConfidence,
  search,
  setSearch,
  sortBy,
  setSortBy,
}: Props) {
  return (
    <div className="bg-white p-4 rounded-lg shadow border mb-4">
      <div className="grid md:grid-cols-3 gap-4">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Tìm kiếm
          </label>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Tìm theo topic..."
            className="w-full p-2 border rounded"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Confidence
          </label>
          <select
            value={confidence}
            onChange={(e) => setConfidence(e.target.value)}
            className="w-full p-2 border rounded"
          >
            <option value="all">Tất cả</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Sắp xếp
          </label>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="w-full p-2 border rounded"
          >
            <option value="gap_desc">Gap Score (cao → thấp)</option>
            <option value="gap_asc">Gap Score (thấp → cao)</option>
            <option value="date_desc">Mới nhất</option>
            <option value="alpha">A-Z</option>
          </select>
        </div>
      </div>
    </div>
  );
}
