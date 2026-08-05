interface PricingItem {
  job_type: string;
  credits: number;
  description: string;
}

const DEFAULT_PRICING: PricingItem[] = [
  { job_type: 'niche_validate', credits: 5, description: 'Validate a YouTube niche' },
  { job_type: 'collect_channel', credits: 10, description: 'Collect metadata + transcripts' },
  { job_type: 'deep_analysis', credits: 50, description: 'Run 14-output deep analysis' },
  { job_type: 'idea_generation', credits: 5, description: 'Generate HDBSCAN-based ideas' },
  { job_type: 'script_generation', credits: 30, description: 'Generate AI script with RAG' },
  { job_type: 'scene_breakdown', credits: 10, description: 'Break script into scenes with B-roll' },
  { job_type: 'rag_retrieve', credits: 1, description: 'RAG context retrieval' },
];

export function PricingTable({ pricing }: { pricing?: PricingItem[] }) {
  const items = pricing || DEFAULT_PRICING;

  return (
    <div className="bg-white rounded-lg shadow border overflow-hidden">
      <div className="p-6 border-b">
        <h2 className="text-xl font-bold">Pricing per Operation</h2>
        <p className="text-sm text-gray-500 mt-1">
          Credits bị trừ mỗi khi chạy job
        </p>
      </div>
      <table className="w-full">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">
              Operation
            </th>
            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">
              Description
            </th>
            <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">
              Credits
            </th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {items.map((item) => (
            <tr key={item.job_type} className="hover:bg-gray-50">
              <td className="px-6 py-4 font-mono text-sm">{item.job_type}</td>
              <td className="px-6 py-4 text-sm text-gray-600">
                {item.description}
              </td>
              <td className="px-6 py-4 text-right">
                <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full font-bold text-sm">
                  {item.credits}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
