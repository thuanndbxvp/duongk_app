# PLAN: Phase 04 — FFmpeg Render & Export

## 1. Mục tiêu
- **Mô tả:** Render video thật từ timeline model; có draft nhanh 720p + final 1080p; progress thật; cancel thật (kill FFmpeg); retry; verify output.
- **Giá trị:** Cốt lõi để xuất bản video.

## 2. Kiến trúc
```text
Timeline JSON (Phase 03)
  → POST /api/projects/{id}/render/draft|final
  → RenderPlanner.compile(timeline, kind) → ffmpeg argv[]
  → enqueue render_video job → celery render queue
  → FFmpegRunner.run(argv, cancel_event, progress_cb)
  → ffprobe verify (streams, duration, codec)
  → Upload R2 → asset_variants row
  → render_jobs.output_asset_id set
```

## 3. Lựa chọn
- **Phương án A — Run FFmpeg shell command trực tiếp (ĐÃ LOẢI):** Không control được progress + cancel.
- **Phương án B — subprocess.Popen + psutil (CHỌN):** Theo dõi stderr, kill được process.
- **Phương án C — ffmpeg-python wrapper (cân nhắc):** Đẹp hơn nhưng ít control khi cancel.

## 4. Rủi ro

| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| FFmpeg process không chết khi cancel | Cao | psutil.Process(pid).terminate() → wait → kill. Verify via Worker registry. |
| Progress fake | Trung bình | Parse stderr `time=00:01:23.45` thực từ FFmpeg. |
| Render lâu chiếm worker | Trung bình | Queue riêng `render`, concurrency max 2, max queue depth 10. |
| Output corrupt | Thấp | ffprobe verify streams, duration, codec. Fail → mark failed. |
| Draft + final conflict | Thấp | Per-project chỉ 1 draft active; final phải đợi draft cancel. |

## 5. Nỗ lực
- ~700 LOC, 9 micro-steps, 5 ngày Tier 2.