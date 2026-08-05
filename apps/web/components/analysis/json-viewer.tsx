'use client';

import { useState } from 'react';

export function JsonViewer({ data }: { data: any }) {
  const [expanded, setExpanded] = useState(false);

  if (data === null || data === undefined) {
    return <span className="text-gray-400 italic">null</span>;
  }

  if (typeof data === 'string' || typeof data === 'number' || typeof data === 'boolean') {
    return <span className="font-mono text-sm">{String(data)}</span>;
  }

  if (Array.isArray(data)) {
    return (
      <div className="font-mono text-sm">
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-blue-600 hover:underline"
        >
          {expanded ? '▼' : '▶'} Array({data.length})
        </button>
        {expanded && (
          <pre className="ml-4 mt-2 bg-gray-50 p-2 rounded overflow-x-auto">
            {JSON.stringify(data, null, 2)}
          </pre>
        )}
      </div>
    );
  }

  // Object
  return (
    <div className="font-mono text-sm">
      <button
        onClick={() => setExpanded(!expanded)}
        className="text-blue-600 hover:underline"
      >
        {expanded ? '▼' : '▶'} Object
      </button>
      {expanded && (
        <pre className="ml-4 mt-2 bg-gray-50 p-2 rounded overflow-x-auto max-h-96">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  );
}
