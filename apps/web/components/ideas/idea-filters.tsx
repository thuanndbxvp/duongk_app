'use client';

import { Select } from '@/components/select';

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
          <Select
            value={confidence}
            onChange={setConfidence}
            options={[
              { value: 'all', label: 'Tất cả' },
              { value: 'high', label: 'High' },
              { value: 'medium', label: 'Medium' },
              { value: 'low', label: 'Low' },
            ]}
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Sắp xếp
          </label>
          <Select
            value={sortBy}
            onChange={setSortBy}
            options={[
              { value: 'gap_desc', label: 'Gap Score (cao → thấp)' },
              { value: 'gap_asc', label: 'Gap Score (thấp → cao)' },
              { value: 'date_desc', label: 'Mới nhất' },
              { value: 'alpha', label: 'A-Z' },
            ]}
          />
        </div>
      </div>
    </div>
  );
}
