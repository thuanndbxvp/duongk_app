'use client';

import { useState } from 'react';
import { OverviewTab } from './overview-tab';
import { DeterministicTab } from './deterministic-tab';
import { NLPTab } from './nlp-tab';
import { LLMTab } from './llm-tab';
import { InsightsTab } from './insights-tab';
import { ThumbnailTab } from './thumbnail-tab';

interface Props {
  data: {
    nlp?: unknown | null;
    llm?: unknown | null;
    deterministic?: unknown | null;
    insights?: unknown | null;
    thumbnail?: unknown | null;
    output?: unknown | null;
  };
}

function countItems(obj: unknown): number {
  if (!obj) return 0;
  if (Array.isArray(obj)) return obj.length;
  if (typeof obj === 'object') return Object.keys(obj).length;
  return 0;
}

type TabDef = { id: string; label: string; count?: number };

export function AnalysisTabs({ data }: Props) {
  const [activeTab, setActiveTab] = useState('overview');

  const counts = {
    deterministic: countItems(data.deterministic),
    nlp: countItems(data.nlp),
    llm: countItems(data.llm),
    insights: countItems(data.insights),
    thumbnail: countItems(data.thumbnail),
  };

  const tabs: TabDef[] = [
    { id: 'overview', label: 'Tổng quan' },
    { id: 'deterministic', label: 'Deterministic', count: counts.deterministic },
    { id: 'nlp', label: 'NLP', count: counts.nlp },
    { id: 'llm', label: 'LLM', count: counts.llm },
    { id: 'insights', label: 'Insights', count: counts.insights },
    { id: 'thumbnail', label: 'Thumbnail', count: counts.thumbnail },
  ];

  return (
    <>
      <div className="border-b border-gray-200 mb-6">
        <div className="flex space-x-1 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 text-sm font-medium whitespace-nowrap transition-colors flex items-center gap-1.5 ${
                activeTab === tab.id
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
              {(tab.count ?? 0) > 0 && (
                <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-semibold ${
                  activeTab === tab.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-600'
                }`}>
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      <div>
        {activeTab === 'overview' && <OverviewTab data={data} />}
        {activeTab === 'deterministic' && (
          <DeterministicTab outputs={(data.deterministic ?? {}) as any} />
        )}
        {activeTab === 'nlp' && <NLPTab outputs={(data.nlp ?? {}) as any} />}
        {activeTab === 'llm' && <LLMTab outputs={(data.llm ?? {}) as any} />}
        {activeTab === 'insights' && <InsightsTab outputs={(data.insights ?? {}) as any} />}
        {activeTab === 'thumbnail' && <ThumbnailTab outputs={(data.thumbnail ?? {}) as any} />}
      </div>
    </>
  );
}