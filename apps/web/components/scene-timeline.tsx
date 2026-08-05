interface Scene {
  scene_number: number;
  start_time: number;
  end_time: number;
  duration_seconds: number;
  text: string;
  broll_translations?: Array<{ en: string; pexels_query: string }>;
}

export function SceneTimeline({ scenes }: { scenes: Scene[] }) {
  if (!scenes || scenes.length === 0) {
    return <p className="text-gray-500 italic">Chưa có phân cảnh nào được tạo.</p>;
  }

  const fmt = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m}:${String(sec).padStart(2, '0')}`;
  };

  return (
    <div className="space-y-4 max-h-[800px] overflow-y-auto pr-2">
      {scenes.map((scene) => (
        <div key={scene.scene_number} className="p-4 border rounded hover:border-blue-300 transition-colors bg-gray-50">
          <div className="flex justify-between items-center mb-3">
            <span className="font-bold text-gray-800">
              Cảnh {scene.scene_number}
            </span>
            <span className="text-sm font-mono bg-white px-2 py-1 rounded border text-gray-600">
              {fmt(scene.start_time)} - {fmt(scene.end_time)}
            </span>
          </div>
          <p className="text-sm text-gray-700 leading-relaxed mb-3">
            {scene.text}
          </p>
          {scene.broll_translations && scene.broll_translations.length > 0 && (
            <div className="pt-3 border-t">
              <p className="text-xs text-gray-500 mb-2 font-semibold">GỢI Ý TÌM KIẾM PEXELS:</p>
              <div className="flex flex-wrap gap-2">
                {scene.broll_translations.map((t, i) => (
                  <span key={i} className="text-xs bg-indigo-100 text-indigo-800 px-2 py-1 rounded shadow-sm">
                    {t.pexels_query}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
