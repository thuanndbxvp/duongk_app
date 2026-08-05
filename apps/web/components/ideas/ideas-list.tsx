'use client';

import { useState, useMemo } from 'react';
import { IdeaCard } from './idea-card';
import { IdeaFilters } from './idea-filters';

interface Idea {
  id: string;
  idea_topic: string;
  gap_score: number;
  cluster_id: number;
  related_topics: string[];
  opportunity_description: string;
  confidence: 'high' | 'medium' | 'low';
}

export function IdeasList({
  ideas,
  assistantId,
}: {
  ideas: Idea[];
  assistantId: string;
}) {
  const [confidence, setConfidence] = useState('all');
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('gap_desc');

  const filteredIdeas = useMemo(() => {
    let result = [...ideas];

    if (confidence !== 'all') {
      result = result.filter((i) => i.confidence === confidence);
    }

    if (search) {
      const s = search.toLowerCase();
      result = result.filter((i) =>
        i.idea_topic.toLowerCase().includes(s)
      );
    }

    switch (sortBy) {
      case 'gap_desc':
        result.sort((a, b) => b.gap_score - a.gap_score);
        break;
      case 'gap_asc':
        result.sort((a, b) => a.gap_score - b.gap_score);
        break;
      case 'date_desc':
        // Assuming newest first by id (UUID v4 has timestamp prefix)
        // Can't reliably sort UUIDs like timestamp, so we'll leave it as is or sort by id string
        result.sort((a, b) => b.id.localeCompare(a.id));
        break;
      case 'alpha':
        result.sort((a, b) => a.idea_topic.localeCompare(b.idea_topic));
        break;
    }

    return result;
  }, [ideas, confidence, search, sortBy]);

  return (
    <>
      <IdeaFilters
        confidence={confidence}
        setConfidence={setConfidence}
        search={search}
        setSearch={setSearch}
        sortBy={sortBy}
        setSortBy={setSortBy}
      />

      <p className="text-sm text-gray-500 mb-3">
        Hiển thị {filteredIdeas.length}/{ideas.length} ideas
      </p>

      {filteredIdeas.length === 0 ? (
        <p className="text-center text-gray-500 italic py-8">
          Không có idea nào khớp với filter.
        </p>
      ) : (
        <div className="space-y-4">
          {filteredIdeas.map((idea) => (
            <IdeaCard
              key={idea.id}
              idea={idea}
              assistantId={assistantId}
            />
          ))}
        </div>
      )}
    </>
  );
}
