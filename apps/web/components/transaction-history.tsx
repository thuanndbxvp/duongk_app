interface Transaction {
  id: string;
  amount: number;  // negative = charge, positive = refund/topup
  job_type?: string;
  metadata?: any;
  created_at: string;
}

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  committed: 'bg-green-100 text-green-800',
  refunded: 'bg-blue-100 text-blue-800',
  done: 'bg-green-100 text-green-800',
};

export function TransactionHistory({
  transactions,
}: {
  transactions: Transaction[];
}) {
  if (transactions.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow border p-8 text-center">
        <p className="text-gray-500">Chưa có giao dịch nào.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow border overflow-hidden">
      <div className="p-6 border-b">
        <h2 className="text-xl font-bold">Transaction History</h2>
        <p className="text-sm text-gray-500 mt-1">
          {transactions.length} giao dịch gần nhất
        </p>
      </div>
      <table className="w-full">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">
              Date
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">
              Type
            </th>
            <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase">
              Amount
            </th>
            <th className="px-4 py-3 text-center text-xs font-semibold text-gray-500 uppercase">
              Status
            </th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {transactions.map((tx) => {
            const status = tx.metadata?.status || 'done';
            const typeLabel =
              tx.job_type || (tx.amount > 0 ? 'topup' : 'unknown');

            return (
              <tr key={tx.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm">
                  {new Date(tx.created_at).toLocaleString('vi-VN')}
                </td>
                <td className="px-4 py-3 text-sm font-mono">{typeLabel}</td>
                <td className="px-4 py-3 text-right">
                  <span
                    className={`font-bold ${
                      tx.amount > 0 ? 'text-green-600' : 'text-red-600'
                    }`}
                  >
                    {tx.amount > 0 ? '+' : ''}
                    {tx.amount}
                  </span>
                </td>
                <td className="px-4 py-3 text-center">
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium ${
                      STATUS_COLORS[status] || 'bg-gray-100 text-gray-800'
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
  );
}
