"use client";

import { useState, useEffect } from "react";

export default function VoiceCloningPage() {
  const [profiles, setProfiles] = useState<any[]>([]);
  const [loadingProfiles, setLoadingProfiles] = useState(true);
  
  const [isUploading, setIsUploading] = useState(false);
  const [uploadName, setUploadName] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  const [selectedVoice, setSelectedVoice] = useState("");
  const [text, setText] = useState("Xin chào, đây là hệ thống nhân bản giọng nói AI.");
  const [isGenerating, setIsGenerating] = useState(false);
  const [resultAudio, setResultAudio] = useState<string | null>(null);

  useEffect(() => {
    fetchProfiles();
  }, []);

  const fetchProfiles = async () => {
    setLoadingProfiles(true);
    try {
      const res = await fetch("/api/voice/profiles");
      const json = await res.json();
      if (json.data) {
        setProfiles(json.data);
        if (json.data.length > 0) setSelectedVoice(json.data[0].id);
      }
    } catch (e) {
      console.error(e);
    }
    setLoadingProfiles(false);
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile || !uploadName) return;
    
    setIsUploading(true);
    const formData = new FormData();
    formData.append("name", uploadName);
    formData.append("file", uploadFile);

    try {
      const res = await fetch("/api/voice/profiles", {
        method: "POST",
        body: formData,
      });
      if (res.ok) {
        setUploadName("");
        setUploadFile(null);
        await fetchProfiles();
      } else {
        const err = await res.json();
        alert("Upload failed: " + JSON.stringify(err));
      }
    } catch (e) {
      alert("Error: " + String(e));
    }
    setIsUploading(false);
  };

  const handleGenerate = async () => {
    if (!selectedVoice || !text) return;
    setIsGenerating(true);
    setResultAudio(null);

    try {
      const res = await fetch("/api/voice/synthesize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, voice_profile_id: selectedVoice }),
      });
      const json = await res.json();
      if (res.ok && json.data) {
        setResultAudio(json.data.audio_url);
      } else {
        alert("Generation failed: " + JSON.stringify(json));
      }
    } catch (e) {
      alert("Error: " + String(e));
    }
    setIsGenerating(false);
  };

  return (
    <main className="container mx-auto p-8 max-w-6xl">
      <h1 className="text-3xl font-bold mb-8">Voice Cloning Studio</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Left Column: Voice Profiles */}
        <div className="md:col-span-1 bg-white p-6 rounded-lg shadow-sm border">
          <h2 className="text-xl font-semibold mb-4">Giọng mẫu (Profiles)</h2>
          
          <form onSubmit={handleUpload} className="mb-6 p-4 bg-gray-50 rounded border border-dashed">
            <h3 className="font-medium mb-2 text-sm text-gray-700">Thêm giọng mới</h3>
            <input 
              type="text" 
              placeholder="Tên giọng (vd: MC Tuấn Anh)" 
              className="w-full mb-2 p-2 border rounded text-sm"
              value={uploadName}
              onChange={(e) => setUploadName(e.target.value)}
              required
            />
            <input 
              type="file" 
              accept=".wav"
              className="w-full mb-3 text-sm"
              onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
              required
            />
            <button 
              type="submit" 
              disabled={isUploading}
              className="w-full bg-blue-600 text-white p-2 rounded text-sm flex items-center justify-center gap-2 disabled:bg-blue-300"
            >
              {isUploading ? "⏳" : "📤"}
              Tải lên
            </button>
            <p className="text-xs text-gray-500 mt-2">Chỉ hỗ trợ file .wav (10-30 giây).</p>
          </form>

          <div className="space-y-3">
            {loadingProfiles ? (
              <p className="text-sm text-gray-500">Đang tải...</p>
            ) : profiles.length === 0 ? (
              <p className="text-sm text-gray-500">Chưa có giọng mẫu nào.</p>
            ) : (
              profiles.map(p => (
                <div key={p.id} className={`p-3 border rounded ${selectedVoice === p.id ? 'border-blue-500 bg-blue-50' : ''}`}>
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-medium text-sm">{p.name}</span>
                  </div>
                  <audio src={p.sample_audio_url} controls className="w-full h-8" />
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Column: Playground */}
        <div className="md:col-span-2 bg-white p-6 rounded-lg shadow-sm border">
          <h2 className="text-xl font-semibold mb-4">Thử nghiệm tạo âm thanh (Playground)</h2>
          
          <div className="mb-4">
            <label className="block text-sm font-medium mb-1">Chọn giọng đọc</label>
            <select 
              className="w-full p-2 border rounded"
              value={selectedVoice}
              onChange={(e) => setSelectedVoice(e.target.value)}
            >
              <option value="" disabled>-- Chọn giọng --</option>
              {profiles.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium mb-1">Văn bản cần đọc (Script)</label>
            <textarea 
              className="w-full p-3 border rounded h-32"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Nhập nội dung vào đây..."
            />
          </div>

          <button 
            onClick={handleGenerate}
            disabled={isGenerating || !selectedVoice || !text}
            className="bg-green-600 text-white px-6 py-2 rounded font-medium flex items-center justify-center gap-2 disabled:bg-gray-400"
          >
            {isGenerating ? "⏳" : "▶️"}
            {isGenerating ? 'Đang gọi GPU xử lý...' : 'Tạo âm thanh'}
          </button>

          {resultAudio && (
            <div className="mt-8 p-6 bg-green-50 border border-green-200 rounded-lg">
              <h3 className="font-medium text-green-800 mb-3">Kết quả:</h3>
              <audio src={resultAudio} controls className="w-full" autoPlay />
              <div className="mt-3 text-sm">
                <a href={resultAudio} target="_blank" className="text-blue-600 hover:underline">Tải xuống file .wav</a>
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
