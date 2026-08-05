interface Props {
  data: any;
}

export function OverviewTab({ data }: Props) {
  const completedOutputs = Object.keys(data?.outputs || {}).length;
  
  return (
    <div className="grid md:grid-cols-3 gap-4">
      <div className="bg-white rounded-lg shadow border p-6">
        <div className="text-sm text-gray-500">14 Outputs</div>
        <div className="text-3xl font-bold mt-1">
          {completedOutputs}/14
        </div>
        <div className="text-xs text-gray-500 mt-1">
          {completedOutputs === 14 ? '✅ Hoàn thành' : '⏳ Đang xử lý'}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow border p-6">
        <div className="text-sm text-gray-500">Lần phân tích cuối</div>
        <div className="text-xl font-bold mt-1">
          {data?.computed_at ? new Date(data.computed_at).toLocaleString('vi-VN') : 'N/A'}
        </div>
        <div className="text-xs text-gray-500 mt-1">
          Version {data?.version || 1}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow border p-6">
        <div className="text-sm text-gray-500">Tổng chi phí</div>
        <div className="text-3xl font-bold mt-1 text-green-600">
          ${(data?.total_cost_usd || 0).toFixed(3)}
        </div>
        <div className="text-xs text-gray-500 mt-1">
          LLM + Vision API
        </div>
      </div>

      <div className="bg-white rounded-lg shadow border p-6 md:col-span-3">
        <h3 className="font-bold mb-3">Output Categories</h3>
        <div className="grid grid-cols-2 md:grid-cols-6 gap-2 text-sm">
          <div className="bg-blue-50 p-3 rounded">
            <div className="font-semibold">Deterministic</div>
            <div className="text-xs">Outputs 1-4</div>
          </div>
          <div className="bg-green-50 p-3 rounded">
            <div className="font-semibold">NLP</div>
            <div className="text-xs">Outputs 5-7</div>
          </div>
          <div className="bg-purple-50 p-3 rounded">
            <div className="font-semibold">LLM</div>
            <div className="text-xs">Outputs 8-11</div>
          </div>
          <div className="bg-orange-50 p-3 rounded">
            <div className="font-semibold">Insights</div>
            <div className="text-xs">Outputs 12-13</div>
          </div>
          <div className="bg-pink-50 p-3 rounded">
            <div className="font-semibold">Thumbnail</div>
            <div className="text-xs">Output 14</div>
          </div>
        </div>
      </div>
    </div>
  );
}
