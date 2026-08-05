export function ScriptEditor({ script }: { script: { hook: string; body: string; cta: string } }) {
  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow border">
        <h2 className="text-xl font-bold mb-4 flex items-center">
          <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm mr-2">1</span> 
          Hook (30 giây)
        </h2>
        <textarea
          value={script.hook}
          readOnly
          className="w-full p-4 border rounded h-32 bg-gray-50 focus:outline-none"
        />
      </div>

      <div className="bg-white p-6 rounded-lg shadow border">
        <h2 className="text-xl font-bold mb-4 flex items-center">
          <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm mr-2">2</span> 
          Nội dung chính (Body)
        </h2>
        <textarea
          value={script.body}
          readOnly
          className="w-full p-4 border rounded h-96 bg-gray-50 focus:outline-none"
        />
      </div>

      <div className="bg-white p-6 rounded-lg shadow border">
        <h2 className="text-xl font-bold mb-4 flex items-center">
          <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm mr-2">3</span> 
          Kêu gọi hành động (CTA)
        </h2>
        <textarea
          value={script.cta}
          readOnly
          className="w-full p-4 border rounded h-24 bg-gray-50 focus:outline-none"
        />
      </div>
    </div>
  );
}
