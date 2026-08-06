interface Transaction {
  id: string;
  amount: number;  // negative = charge, positive = refund/topup
  job_type?: string;
  metadata?: any;
  created_at: string;
}

const STATUS_STYLES: Record<string, string> = {
  pending:
    'bg-yellow-500/10 text-yellow-300 border border-yellow-500/30',
  committed:
    'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30',
  refunded:
    'bg-sky-500/10 text-sky-300 border border-sky-500/30',
  done:
    'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30',
};

export function TransactionHistory({
  transactions,
}: {
  transactions: Transaction[];
}) {
  if (transactions.length === 0) {
    return (
      <section className="glass-strong rounded-2xl p-10 text-center">
        <p className="text-[var(--fg-secondary)]">Chưa có giao dịch nào.</p>
      </section>
    );
  }

  return (
    <section className="relative glass-strong rounded-2xl overflow-hidden">
      <div
        aria-hidden
        className="pointer-events-none absolute -top-20 -right-20 h-48 w-48 rounded-full bg-[var(--brand-500)] opacity-15 blur-3xl"
      />
      <div className="relative p-7 border-b border-[var(--glass-border)]">
        <h2 className="text-lg font-semibold text-white">Transaction History</h2>
        <p className="text-sm text-[var(--fg-secondary)] mt-1">
          {transactions.length} giao dịch gần nhất
        </p>
      </div>

      <div className="relative overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[var(--glass-border)]">
              <th className="px-6 py-3 text-left text-xs font-semibold text-[var(--fg-tertiary)] uppercase tracking-wider">
                Date
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-[var(--fg-tertiary)] uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-[var(--fg-tertiary)] uppercase tracking-wider">
                Amount
              </th>
              <th className="px-6 py-3 text-center text-xs font-semibold text-[var(--fg-tertiary)] uppercase tracking-wider">
                Status
              </th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((tx) => {
              const status = tx.metadata?.status || 'done';
              const typeLabel =
                tx.job_type || (tx.amount > 0 ? 'topup' : 'unknown');
              const isPositive = tx.amount > 0;

              return (
                <tr
                  key={tx.id}
                  className="border-b border-[var(--glass-border)] last:border-b-0 hover:bg-white/[0.03] transition"
                >
                  <td className="px-6 py-3 text-sm text-[var(--fg-secondary)]">
                    {new Date(tx.created_at).toLocaleString('vi-VN')}
                  </td>
                  <td className="px-6 py-3 text-sm font-mono text-[var(--brand-300)]">
                    {typeLabel}
                  </td>
                  <td className="px-6 py-3 text-right">
                    <span
                      className={`font-bold ${
                        isPositive ? 'text-emerald-400' : 'text-[var(--danger)]'
                      }`}
                    >
                      {isPositive ? '+' : ''}
                      {tx.amount.toLocaleString('vi-VN')}
                    </span>
                  </td>
                  <td className="px-6 py-3 text-center">
                    <span
                      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
                        STATUS_STYLES[status] ||
                        'bg-white/[0.06] text-[var(--fg-secondary)] border border-[var(--glass-border)]'
                      }`}
                    >
                      {status}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}