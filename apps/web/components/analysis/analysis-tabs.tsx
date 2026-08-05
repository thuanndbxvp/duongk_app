'use client';

import { useState } from 'react';
import { OverviewTab } from './overview-tab';
import { DeterministicTab } from './deterministic-tab';
import { NLPTab } from './nlp-tab';
import { LLMTab } from './llm-tab';
import { InsightsTab } from './insights-tab';
import { ThumbnailTab } from './thumbnail-tab';

interface Props {
  data: any;
}

const TABS = [
  { id: 'overview', label: 'Tổng quan' },
  { id: 'deterministic', label: 'Deterministic' },
  { id: 'nlp', label: 'NLP' },
  { id: 'llm', label: 'LLM' },
  { id: 'insights', label: 'Insights' },
  { id: 'thumbnail', label: 'Thumbnail' },
];

export function AnalysisTabs({ data }: Props) {
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <>
      <div className="border-b border-gray-200 mb-6">
        <div className="flex space-x-1 overflow-x-auto">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 text-sm font-medium whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        {activeTab === 'overview' && <OverviewTab data={data} />}
        {activeTab === 'deterministic' && (
          <DeterministicTab outputs={data.outputs || {}} />
        )}
        {activeTab === 'nlp' && <NLPTab outputs={data.outputs || {}} />}
        {activeTab === 'llm' && <LLMTab outputs={data.outputs || {}} />}
        {activeTab === 'insights' && <InsightsTab outputs={data.outputs || {}} />}
        {activeTab === 'thumbnail' && <ThumbnailTab outputs={data.outputs || {}} />}
      </div>
    </>
  );
}
