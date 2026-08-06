'use client';

interface Insight {
  id: string;
  title: string;
  body: string;
  evidence_comment_ids: string[];
  opportunity_score: number | null;
  status: string;
}

interface Props {
  insight: Insight;
  onApprove?: (id: string) => void;
  onReject?: (id: string) => void;
  onToProject?: (id: string) => void;
}

export function InsightCard({ insight, onApprove, onReject, onToProject }: Props) {
  return (
    <div className="glass-strong rounded-xl p-4 space-y-3 hover:border-[var(--brand-400)]/30 transition">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h4 className="font-semibold text-sm">{insight.title}</h4>
          <p className="text-xs text-[var(--fg-secondary)] mt-1">{insight.body}</p>
        </div>
        {insight.opportunity_score != null && (
          <span className="text-xs px-2 py-0.5 rounded bg-green-500/10 text-green-400 ml-2 shrink-0">
            {(insight.opportunity_score * 100).toFixed(0)}%
          </span>
        )}
      </div>

      {/* Evidence chips */}
      {insight.evidence_comment_ids.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {insight.evidence_comment_ids.slice(0, 3).map((eid, i) => (
            <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400">
              📝 {eid.slice(0, 8)}...
            </span>
          ))}
          {insight.evidence_comment_ids.length > 3 && (
            <span className="text-[10px] text-[var(--fg-tertiary)]">
              +{insight.evidence_comment_ids.length - 3} more
            </span>
          )}
        </div>
      )}

      {/* Status + Actions */}
      <div className="flex items-center justify-between">
        <span className={`text-xs px-2 py-0.5 rounded ${
          insight.status === 'approved' ? 'bg-green-500/20 text-green-400' :
          insight.status === 'applied' ? 'bg-purple-500/20 text-purple-400' :
          insight.status === 'rejected' ? 'bg-red-500/20 text-red-400' :
          'bg-yellow-500/20 text-yellow-400'
        }`}>{insight.status}</span>

        {insight.status === 'pending' && (
          <div className="flex gap-2">
            <button onClick={() => onApprove?.(insight.id)}
              className="text-xs px-2 py-1 rounded bg-green-500/10 text-green-400 hover:bg-green-500/20">✓ Approve</button>
            <button onClick={() => onReject?.(insight.id)}
              className="text-xs px-2 py-1 rounded bg-red-500/10 text-red-400 hover:bg-red-500/20">✕ Reject</button>
          </div>
        )}
        {insight.status === 'approved' && (
          <button onClick={() => onToProject?.(insight.id)}
            className="text-xs px-2 py-1 rounded gradient-bg text-white">→ Create Project</button>
        )}
      </div>
    </div>
  );
}
