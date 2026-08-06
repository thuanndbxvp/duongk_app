interface PricingItem {
  job_type: string;
  credits: number;
  description: string;
}

const DEFAULT_PRICING: PricingItem[] = [
  { job_type: 'niche_validate', credits: 5, description: 'Xác thực niche YouTube' },
  { job_type: 'collect_channel', credits: 10, description: 'Thu thập metadata + transcripts' },
  { job_type: 'deep_analysis', credits: 50, description: 'Chạy phân tích sâu 14 output' },
  { job_type: 'idea_generation', credits: 5, description: 'Sinh ý tưởng theo HDBSCAN' },
  { job_type: 'script_generation', credits: 30, description: 'Sinh kịch bản AI với RAG' },
  { job_type: 'scene_breakdown', credits: 10, description: 'Tách kịch bản thành các cảnh + B-roll' },
  { job_type: 'rag_retrieve', credits: 1, description: 'Truy xuất ngữ cảnh RAG' },
];

export function PricingTable({ pricing }: { pricing?: PricingItem[] }) {
  const items = pricing || DEFAULT_PRICING;

  return (
    <section className="relative glass-strong rounded-2xl overflow-hidden">
      <div
        aria-hidden
        className="pointer-events-none absolute -top-20 -right-20 h-48 w-48 rounded-full bg-[var(--brand-500)] opacity-15 blur-3xl"
      />
      <div className="relative p-7 border-b border-[var(--glass-border)]">
        <h2 className="text-lg font-semibold text-white">Bảng giá theo tác vụ</h2>
        <p className="text-sm text-[var(--fg-secondary)] mt-1">
          Credits bị trừ mỗi khi chạy job.
        </p>
      </div>

      <div className="relative overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[var(--glass-border)]">
              <th className="px-6 py-3 text-left text-xs font-semibold text-[var(--fg-tertiary)] uppercase tracking-wider">
                Tác vụ
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-[var(--fg-tertiary)] uppercase tracking-wider">
                Mô tả
              </th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-[var(--fg-tertiary)] uppercase tracking-wider">
                Credits
              </th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr
                key={item.job_type}
                className="border-b border-[var(--glass-border)] last:border-b-0 hover:bg-white/[0.03] transition"
              >
                <td className="px-6 py-4 font-mono text-sm text-[var(--brand-300)]">
                  {item.job_type}
                </td>
                <td className="px-6 py-4 text-sm text-[var(--fg-secondary)]">
                  {item.description}
                </td>
                <td className="px-6 py-4 text-right">
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-white/[0.06] border border-[var(--glass-border)] text-white">
                    {item.credits}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}