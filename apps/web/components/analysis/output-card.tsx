import { JsonViewer } from './json-viewer';

interface OutputCardProps {
  number: number;
  title: string;
  description: string;
  data: any;
  cost?: number;
}

export function OutputCard({ number, title, description, data, cost }: OutputCardProps) {
  return (
    <div className="bg-white rounded-lg shadow border p-6">
      <div className="flex items-start justify-between mb-3">
        <div>
          <span className="text-xs font-semibold bg-blue-100 text-blue-800 px-2 py-1 rounded">
            Output #{number}
          </span>
          <h3 className="text-lg font-bold mt-2">{title}</h3>
          <p className="text-sm text-gray-500">{description}</p>
        </div>
        {cost !== undefined && cost > 0 && (
          <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
            ${cost.toFixed(3)}
          </span>
        )}
      </div>
      <div className="mt-4">
        <JsonViewer data={data} />
      </div>
    </div>
  );
}
