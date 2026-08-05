'use client';

import { useEffect, useState } from 'react';
import { SceneTimeline } from '@/components/scene-timeline';

interface Script {
  id: string;
  topic: string;
  script: { title: string; hook: string; body: string; cta: string };
  scenes: any[];
}

export default function ScriptEditorPage({ params }: { params: Promise<{ id: string }> }) {
  const [script, setScript] = useState<Script | null>(null);

  useEffect(() => {
    async function fetchScript() {
      const resolvedParams = await params;
      // Using direct fetch assuming we will build an API route for script if needed, 
      // or we can use Supabase client directly.
      // Wait, let's assume we have a GET /api/scripts/[id] in FastAPI.
      // We didn't build a proxy for /api/scripts/[id] in Next.js yet, so let's call FastAPI directly or Supabase.
      // Actually, since we have RLS enabled, we can just use Supabase client.
      const { createBrowserClient } = await import('@supabase/ssr');
      const supabase = createBrowserClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
      );
      
      const { data } = await supabase
        .from('generated_scripts')
        .select('*')
        .eq('id', resolvedParams.id)
        .single();
        
      if (data) {
        setScript(data as Script);
      }
    }
    fetchScript();
  }, [params]);

  if (!script) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  );

  return (
    <main className="container mx-auto p-8">
      <div className="mb-8 border-b pb-4">
        <h1 className="text-3xl font-bold mb-2">{script.script.title}</h1>
        <p className="text-gray-600">
          <span className="font-semibold text-gray-800">Chủ đề:</span> {script.topic}
        </p>
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow border">
            <h2 className="text-xl font-bold mb-4 flex items-center">
              <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm mr-2">1</span> 
              Hook (30 giây)
            </h2>
            <textarea
              value={script.script.hook}
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
              value={script.script.body}
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
              value={script.script.cta}
              readOnly
              className="w-full p-4 border rounded h-24 bg-gray-50 focus:outline-none"
            />
          </div>
        </div>

        <div>
          <div className="bg-white p-6 rounded-lg shadow border sticky top-8">
            <h2 className="text-xl font-bold mb-6 flex items-center">
              <span className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm mr-2">B-roll</span> 
              Gợi ý Cảnh quay (Scenes)
            </h2>
            <SceneTimeline scenes={script.scenes || []} />
          </div>
        </div>
      </div>
    </main>
  );
}
