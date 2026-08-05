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
    <main className="container mx-auto p-8 max-w-6xl text-[#f9fafb]">
      <h1 className="text-3xl font-bold mb-8 text-white">Voice Cloning Studio</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Left Column: Voice Profiles */}
        <div className="md:col-span-1 bg-[#1f2937] p-6 rounded-xl border border-[#374151]">
          <h2 className="text-xl font-semibold mb-4 text-white">Giọng mẫu (Profiles)</h2>
          
          <form onSubmit={handleUpload} className="mb-6 p-4 bg-[#111827] rounded-lg border border-dashed border-[#374151]">
            <h3 className="font-medium mb-2 text-sm text-[#9ca3af]">Thêm giọng mới</h3>
            <input 
              type="text" 
              placeholder="Tên giọng (vd: MC Tuấn Anh)" 
              className="w-full mb-3 p-3 bg-[#111827] border border-[#374151] rounded-lg text-sm text-[#f9fafb] focus:border-[#3b82f6] outline-none"
              value={uploadName}
              onChange={(e) => setUploadName(e.target.value)}
              required
            />
            <input 
              type="file" 
              accept=".wav"
              className="w-full mb-4 text-sm text-[#9ca3af] file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-[#3b82f6] file:text-white hover:file:bg-[#2563eb] cursor-pointer"
              onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
              required
            />
            <button 
              type="submit" 
              disabled={isUploading}
              className="w-full bg-[#3b82f6] hover:bg-[#2563eb] text-white py-2.5 rounded-lg text-sm font-semibold flex items-center justify-center gap-2 disabled:opacity-60 transition-colors"
            >
              {isUploading ? "⏳" : "📤"}
              Tải lên
            </button>
            <p className="text-xs text-[#9ca3af] mt-3">Chỉ hỗ trợ file .wav (10-30 giây).</p>
          </form>

          <div className="space-y-3">
            {loadingProfiles ? (
              <p className="text-sm text-[#9ca3af]">Đang tải...</p>
            ) : profiles.length === 0 ? (
              <p className="text-sm text-[#9ca3af]">Chưa có giọng mẫu nào.</p>
            ) : (
              profiles.map(p => (
                <div key={p.id} className={`p-3 border rounded-lg ${selectedVoice === p.id ? 'border-[#3b82f6] bg-[rgba(59,130,246,0.15)]' : 'border-[#374151] bg-[#111827]'}`}>
                  <div className="flex justify-between items-center mb-2">
                    <span className={`font-medium text-sm ${selectedVoice === p.id ? 'text-[#3b82f6]' : 'text-[#f9fafb]'}`}>{p.name}</span>
                  </div>
                  <audio src={p.sample_audio_url} controls className="w-full h-8" />
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Column: Playground */}
        <div className="md:col-span-2 bg-[#1f2937] p-6 rounded-xl border border-[#374151]">
          <h2 className="text-xl font-semibold mb-6 text-white">Thử nghiệm tạo âm thanh (Playground)</h2>
          
          <div className="mb-5">
            <label className="block text-sm font-semibold mb-2 text-[#9ca3af]">Chọn giọng đọc</label>
            <select 
              className="w-full p-3 bg-[#111827] border border-[#374151] rounded-lg text-[#f9fafb] focus:border-[#3b82f6] outline-none"
              value={selectedVoice}
              onChange={(e) => setSelectedVoice(e.target.value)}
            >
              <option value="" disabled>-- Chọn giọng --</option>
              {profiles.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-semibold mb-2 text-[#9ca3af]">Văn bản cần đọc (Script)</label>
            <textarea 
              className="w-full p-4 bg-[#111827] border border-[#374151] rounded-lg h-40 text-[#f9fafb] focus:border-[#3b82f6] outline-none resize-none leading-relaxed"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Nhập nội dung vào đây..."
            />
          </div>

          <button 
            onClick={handleGenerate}
            disabled={isGenerating || !selectedVoice || !text}
            className="bg-[#10b981] hover:bg-[#059669] text-white px-8 py-3 rounded-lg font-semibold flex items-center justify-center gap-2 disabled:opacity-60 transition-colors"
          >
            {isGenerating ? "⏳" : "▶️"}
            {isGenerating ? 'Đang gọi GPU xử lý...' : 'Tạo âm thanh'}
          </button>

          {resultAudio && (
            <div className="mt-8 p-6 bg-[rgba(16,185,129,0.1)] border border-[#10b981] rounded-xl">
              <h3 className="font-semibold text-[#10b981] mb-4">✨ Kết quả sinh âm thanh:</h3>
              <audio src={resultAudio} controls className="w-full outline-none" autoPlay />
              <div className="mt-4 text-sm">
                <a href={resultAudio} target="_blank" className="text-[#3b82f6] hover:text-[#2563eb] hover:underline font-medium">⬇️ Tải xuống file .wav</a>
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
