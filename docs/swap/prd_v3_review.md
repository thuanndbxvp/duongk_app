# 📋 Review PRD v3 — YouTube AI SaaS (Channel Cloning Platform)

> **Ngày review:** 2026-08-05
> **Reviewer:** Cursor AI (grok-4.5)
> **Source:** `docs/prd_v3.md` (1652 dòng)
> **Mục đích:** Đánh giá tính khả thi, tính chi tiết, liệt kê điểm mờ cần làm rõ trước khi bắt tay vào code.

---

## 1. TỔNG QUAN

PRD v3 là bản kế thừa có chọn lọc từ `prd_v2.md` (~4366 dòng), tích hợp thêm 2 file nghiên cứu:

- **`ana_plan1.md`** — phân tích quy trình 5 bước của OverseerOS
- **`ana_plan2.md`** — báo cáo 11 screenshot áp dụng cho kênh "Chú Béo Tài Chính"

### Trọng tâm chính của v3 (từ header §0):

> *"(1) YouTube Data Collection, (2) Style/Tone DNA NLP Analysis, (3) Metadata/Tags/Ý tưởng — kèm 9 Appendix để AI Coding (Cursor/Cline) có thể sinh code chạy được ~95% mà không cần đoán thêm."*

### Cấu trúc PRD v3:

| Phần | Nội dung | Số section |
|------|----------|------------|
| **PART I — Foundation** | Tech stack, monorepo, DB schema, RLS, API, Auth, Realtime, Credit system | §1-§9 |
| **PART II — Core Pipeline** | 13 outputs OverseerOS-style, 5 module 2A→2E | §10-§17 |
| **PART III — Appendices** | A (Formulas) → J (Sprint Roadmap) | 9 appendices |

Tổng: **28 sections + 9 appendices**, **1652 dòng**, ước tính ~95KB.

---

## 2. ĐIỂM MẠNH (v3 tốt hơn v2 rất nhiều)

### 2.1. Cấu trúc tách bạch cực rõ

3 phần rõ ràng (Foundation → Pipeline → Appendices) → AI coding không bị lạc. 9 appendices chi tiết → đúng tinh thần "AI Coding chạy được 95% không phải đoán" mà header §0 cam kết.

### 2.2. Phân biệt 3 loại xử lý — chống over-LLM

**Appendix D (Deterministic vs LLM vs Local-ML Task Matrix)** là highlight lớn nhất:

- **v2**: nhét hết vào LLM (đắt, không nhất quán)
- **v3**: ép **23/40 task dùng Python deterministic** + **6 task dùng Local ML** (HF/PhoBERT/VADER/textstat)

→ Tiết kiệm ~$0.20-0.30/analysis và reproducible.

### 2.3. 15 công thức toán học cụ thể (Appendix A)

| Công thức | Tên | Mục đích |
|-----------|-----|----------|
| **A1** | Niche Viability | is_viable_niche(): check 5M views + 3M trend |
| **A2** | Viral per-channel | outlier_strength(v) = (views - median) / MAD |
| **A3** | Viral in niche | views ≥ 3 × niche_median (cho Module 1) |
| **A4** | Optimal Duration | percentile(durations, 25/75) trên viral videos |
| **A5** | Consistency Score | 100 × (1 - cv) với cv = stdev/mean gaps |
| **A6** | Optimal Tag Count | mode(len(tags)) trên viral videos |
| **A7** | Tag Co-occurrence | Counter với combinations(sorted(tags), 2) |
| **A8** | Signature Phrase Extraction | TF-IDF ngram(3,8) vs baseline corpus |
| **A9** | Hook Density | percentile(gaps, 10/90) giữa các hooks |
| **A10** | Emotional Curve | split 10 segments → RoBERTa classify |
| **A11** | Structural Boundary | find_local_minima(cos_sim) |
| **A12** | Success Formula Detection | chi-square test (p<0.05) |
| **A13** | WPM Calculation | words / (duration / 60) |
| **A14** | Gap Score (Untapped) | 0.5 × channel_dist + 0.5 × trending_dist |
| **A15** | Slop Score (Anti-AI) | hits × 15, threshold > 40 |

→ Đây là thay thế hoàn toàn "magic number" trong v2.

### 2.4. YouTube quota rotation + cache stampede prevention (Appendix B)

- B1: Quota cost table (search.list = 100, videos.list = 1)
- B2: Feature cost estimate (Deep collection ≈ 10-12 units / 200 videos)
- B3: Daily budget (5 keys × 10K = 50K units/day → ~450 niche validations/ngày)
- B4: Circuit breaker (80% → degraded mode)

→ Đây là **điểm yếu chí mạng của v2** đã được vá triệt để.

### 2.5. External API 3-tier fallback matrix (Appendix C)

| Purpose | Tier 1 (free) | Tier 2 (paid) | Tier 3 (last resort) |
|---------|---------------|---------------|----------------------|
| Transcript | youtube-transcript-api | Supadata ($0.001/min) | yt-dlp + Whisper ($0.006/min) |
| Video footage | Pexels | Pixabay | Unsplash + Ken Burns |
| Trends | pytrends (unofficial) | SerpAPI ($75/mo) | Skip + warn |
| LLM | GPT-4o | Gemini 1.5 Pro | Claude 3.5 Sonnet |
| Embeddings | text-embedding-3-small | Cohere multilingual | intfloat/e5-large (local) |
| Emotion classifier | j-hartmann | PhoBERT-emotion-vn | LLM (expensive) |

→ Rất rõ ràng cho production stability.

### 2.6. Legal / ToS compliance (Appendix I)

v3 có, v2 không có → quan trọng cho go-to-market:

- I1: Chỉ dùng YouTube Data API v3, không scrape HTML
- I2: Whisper transcription "fair use for analysis, not redistribute"
- I3: Pexels/Unsplash attribution rules (Unsplash **bắt buộc** ghi photographer)
- I4: User owns generated scripts NHƯNG disclaimer overlap
- I5: GDPR — delete all data within 30 days

### 2.7. Cost model + BYOK (Appendix H)

Giả định **1 credit = $0.01**, target margin 60-70%:

| Action | Cost | Giá bán | Margin |
|--------|------|---------|--------|
| Niche validate | $0.02 | 5 credits | 60% |
| Deep channel analysis (13 outputs) | $0.35 | 100 credits | 65% |
| Transcript fetch (~15min) | $0.09 | 10 credits | **10%** ⚠️ |
| Script generation (2500 words) | $0.055 | 20 credits | 72% |
| Scene breakdown (40 scenes) | $0.02 | 10 credits | 80% |
| Thumbnail analysis | $0.02 | 5 credits | 60% |

Full journey: **185 credits ≈ $1.85 to user / $0.60 cost → margin ~68%**.

### 2.8. 13 Outputs phân lớp đầy đủ

| # | Output | Layer | Tool | Phụ thuộc |
|---|--------|-------|------|-----------|
| 1 | Metadata Report | Deterministic | Python + numpy | Raw video list |
| 2 | Tags Report | Deterministic | Python + Counter | Raw video list |
| 3 | Performance Report | Deterministic | Python + statistics | Raw video list |
| 4 | Hidden Insights | Deterministic + LLM narrate | Python stats → LLM | Output 1,2,3 |
| 5 | Persona | LLM | GPT-4o | Transcripts (viral) |
| 6 | Pacing Profile | Deterministic + Local NLP | Python + underthesea | Transcripts |
| 7 | Emotional Signature | Local ML | RoBERTa emotion | Transcripts |
| 8 | Hook Analysis | LLM + Regex | GPT-4o + regex | Transcripts (first 30s) |
| 9 | Structural Formula | LLM + rule-check | GPT-4o | Transcripts (full) |
| 10 | Signature Phrases | Deterministic + LLM | n-gram TF-IDF → LLM | Transcripts |
| 11 | Mimic Rules | LLM (constrained) | GPT-4o | Outputs 5-10 |
| 12 | Viral Topics Formula | LLM + Clustering | Embed cluster → LLM | Top-K viral titles |
| 13 | Untapped Opportunities | LLM + Gap Analysis | Embed gap → LLM | Outputs 1,2,12 + Trends |

Bonus (không đánh số): Thumbnail Analysis (Vision LLM), Content Calendar.

---

## 3. ĐIỂM MỜ / MÂU THUẪN CẦN LÀM RÕ

Phát hiện **12 điểm** chia 3 nhóm: 🔴 Critical (block code), 🟡 Quan trọng (block prompt viết), 🟢 Nice-to-have.

### 🔴 NHÓM A — CRITICAL (block code ngay)

#### A1. Mâu thuẫn Appendix G vs §10 — "Thumbnail Analysis" bị tách khỏi 13 outputs

**Vấn đề:**
- §10 liệt kê 13 outputs đánh số 1-13, **không bao gồm** Thumbnail Analysis
- Nhưng DAG Appendix G hiển thị Thumbnail Analysis như node độc lập (cùng cấp với #5-9)
- §17 cũng nói Module 3 "giữ nguyên từ v2 có bổ sung"
- Appendix D row #29 có "Thumbnail analysis" → gán LLM Vision
- Bảng `channel_deep_analysis` đã có column `thumbnail_analysis JSONB`

**Cần làm rõ:**
- Thumbnail Analysis là output **#14 bonus** hay là 1 phần của output #8 (Hook Analysis)?
- Nếu bonus → DAG cần update
- Nếu part of #8 → DAG cần update

**Recommend:** Output số **#14 bonus**, chạy song song batch 2 (#5-10) trong DAG.

---

#### A2. Mâu thuẫn Formula A2 vs A3 — nhầm cross-reference

**Vấn đề:**
- §13.3 nói: *"outlier_strength(v) = (v.views - median_views_of_channel)..."* → **per-channel** definition
- Nhưng Appendix A3 lại đặt tên là "Viral Video (**across niche**)" với formula `v.views >= 3 * niche_median_views` → **per-niche** definition
- §12.2 Step 6 lại nói *"Rank by outlier_strength (see Appendix A, Formula A3)"* → **nhầm A2 với A3**

**Cần làm rõ:** Cross-reference giữa §13.3, A2, A3, §12.2 Step 6.

**Recommend:**
- A2 = "Viral per channel" (cho Deep Analysis, dùng `outlier_strength`)
- A3 = "Viral in niche" (cho Module 1, dùng `3 × niche_median`)
- §12.2 Step 6 phải sửa thành *"Rank by outlier_strength (see Appendix A2)"*

---

#### A3. Step 8 Module 1 đánh số sai

**Vấn đề:**
- §11.2 liệt kê "Step 1, 2, 3, 4, 5, 6, 7" → 7 bước
- Nhưng có "Step 8: [Parallel] Fetch Google Trends..."
- Và "Step 9: LLM → generate 5 title ideas"
- Và "Step 10: Cache result 24h + save to market_research table"
- Tổng cộng **10 steps**, không phải 7 như tiêu đề §11.2 nói

**Cần làm rõ:** Tiêu đề nói "7 steps" nhưng thực tế 10.

**Recommend:** Sửa tiêu đề thành *"Pipeline (10 steps)"* hoặc gộp Steps 8-10 thành "Phase 2: parallel fetch + finalize".

---

#### A4. Module 2B thiếu UI/UX flow

**Vấn đề:**
- §13 mô tả 4 outputs deterministic (Metadata, Tags, Performance, Hidden Insights)
- Nhưng **không nói** ai trigger, khi nào UI hiển thị:
  - Sau khi user submit channel URL → show progress bar realtime cho 4 outputs?
  - Hay chạy ngầm, chỉ hiển thị kết quả cuối?
  - Hidden Insights cần LLM "narrate" — step này nằm ở UI state nào?

**Cần làm rõ:** Blueprint Progress (v2 Module 2D, v3 Module 2A-2E) — UI hiển thị step deterministic realtime, hay chỉ show "Analyzing..." spinner?

**Recommend:** Show progress per output (1/13 → 2/13 → ... → 13/13) thay vì spinner mù. Mỗi output có thời gian ước tính.

---

### 🟡 NHÓM B — QUAN TRỌNG (block prompt E2-E7)

#### B1. Embedding model cho VN: chưa chốt 100%

**Vấn đề:**
- §1 Tech Stack: `"text-embedding-3-small" (default) + "Cohere embed-multilingual-v3" (VN) | Auto-detect language`
- Appendix C row "Embeddings": `text-embedding-3-small` (EN + VN partial) → fallback Cohere → fallback local `intfloat/multilingual-e5-large`

**Mâu thuẫn nhỏ:** "Auto-detect language" ở §1 nhưng Appendix C không nói rõ detect bằng cách nào.

**Quan trọng vì:** OpenAI embedding cho VN chất lượng kém hơn EN ~15-20% (theo independent benchmarks).

**Cần làm rõ:**
- Logic auto-detect nằm ở đâu? (có thể dùng `langdetect` trên 500 chars đầu)
- Có cache kết quả detection không?
- Có override manual trong UI không (user tick "force VN embed")?

---

#### B2. RAG section filter — schema có nhưng SQL chưa thấy

**Vấn đề:**
- §14.3 dùng RPC `match_dna_chunks` với `section_filter` parameter:
  ```python
  supabase.rpc('match_dna_chunks', {
      'query_embedding': topic_emb,
      'assistant_id': assistant_id,
      'section_filter': target_section,
      'match_threshold': 0.65,
      'match_count': 20
  })
  ```
- §3.2 schema `dna_chunks` CÓ column `section` (hook/body/analogy/cta/transition) ✓
- Nhưng SQL function `match_dna_chunks` exact chưa thấy trong v3 (có thể tách sang migration riêng)

**Cần làm rõ:** SQL function `match_dna_chunks` có nhận `section_filter` không? Nếu có, syntax exact (Postgres function signature)?

---

#### B3. Anti-AI-Slop 3-layer enforcement — LLM validator chưa rõ

**Vấn đề:** §14.4 nói:
> 3. **LLM validator (Phase 2):** dedicated pass that scores output 0-100 for "AI-ness" → reject if score > 60.

Nhưng:
- "AI-ness" định nghĩa thế nào? Prompt cụ thể?
- Cost của validator mỗi lần ~$0.005-0.01 → +5-10% mỗi script generation
- Phase 2 — vậy **Phase 1 chỉ có 2 layer** (in-prompt + regex)?

**Cần làm rõ:**
- Phase 1 có 2 layer đủ chưa (in-prompt + regex post-check)?
- Phase 2 validator prompt nội dung thế nào? (chưa có trong Appendix E)

**Recommend:** Thêm prompt E9 (ANTI_SLOP_LLM_VALIDATOR_PROMPT) với scoring rubric cụ thể.

---

#### B4. Prompt E2 (STYLE_DNA_PROMPT_V3) chưa có example_output baseline

**Vấn đề:** Appendix E2 mô tả structure JSON output, nhưng thiếu:
- Example output cho 1 channel thật (dùng Chú Béo case từ `ana_plan2.md` làm regression test baseline)
- Constraints cho `tone_archetype` enum (đã list 5, nhưng liệu có đủ?)
- Quy tắc khi LLM không tìm được persona rõ ràng → fallback gì?

**Recommend:** Thêm **E2.1 Example Output** đầy đủ với persona + 9-step formula + 11 mimic rules dựa trên Chú Béo Tài Chính.

---

### 🟢 NHÓM C — NICE-TO-HAVE (không block code, ảnh hưởng UX/scale)

#### C1. pytrends — rate limit & reliability

- `pytrends` **unofficial**, Google có thể block IP bất cứ lúc nào
- Khi dùng cho mọi Module 1 job sẽ rất mong manh

**Cần làm rõ:**
- Có dùng residential proxy cho pytrends không? (cost thêm)
- Có rate limit riêng (1 req / 5s)?
- Khi pytrends fail 100% → có skip và warn user không? (Appendix C có nói "Skip + warn user" ✓)

**Recommend:** Thêm cache **7 ngày** cho pytrends results (giảm 90% call).

---

#### C2. Vietnamese HF emotion model — `wonrax/phobert-base-vietnamese-emotion`

- §1 + F4 đề cập model này
- Cần verify: Model có thật trên HuggingFace không? License cho phép dùng commercial? 7-class output có khớp Appendix A10?

**Cần làm rõ:** Link model + license.

**Recommend:** Verify trong Sprint 2 trước khi commit; fallback sang translate VN→EN + j-hartmann nếu fail.

---

#### C3. Module 1 "top_channels: 10-100" — chọn kiểu nào?

- §11.3 Output schema: `top_channels: Channel[]; // top 10-100`
- Tại sao range?
- Có phải user upgrade tier để lấy 100?
- Hay default 10, click "Xem thêm" để load 100?

**Cần làm rõ:** Phân biệt default vs on-demand.

**Recommend:** Default 10, button "Load 10 more" × N, cap 100.

---

#### C4. Cost model "Transcription 10 credits" có margin quá mỏng (10%)

- Appendix H1: *"Transcript fetch (per video, ~15 min): $0.09 (Whisper worst-case) → 10 credits ($0.10) → Margin 10% (thin margin, needs tier 1 success rate 80%+)"*
- Tức là app CẦN tier 1 (youtube-transcript-api) thành công ≥80% thì mới có lãi
- Whisper cho audio 15min ~$0.09 → margin = 10%

**Cần làm rõ:**
- Có chính sách giảm credit nếu transcript < 5min (Whisper cost thấp hơn)?
- Có option "Skip transcript" cho user (chỉ analyze metadata)?

**Recommend:** Phân loại transcript theo tier:
- Tier 1 success → 5 credits
- Tier 3 (Whisper) → 15 credits

---

#### C5. Cache strategy "transcripts Permanent" có vi phạm YouTube ToS?

- §12.4: *"Transcript: Postgres `transcripts` table | Permanent | Never"*
- Appendix I1: *"Cache expiration: comply with YouTube API TOS (do not permanently store data)"*

**Mâu thuẫn.**

**Recommend:** Phân biệt rõ:
- **Cache data từ YouTube Data API** (video metadata, statistics): TTL 24h
- **Transcripts** (do user generate qua youtube-transcript-api HOẶC Whisper): OK lưu vĩnh viễn vì là data do mình xử lý, không phải trực tiếp từ API.

---

## 4. ĐÁNH GIÁ TÍNH KHẢ THI KỸ THUẬT

### 4.1. Tính khả thi CAO (sẵn sàng code)

| Hạng mục | Verdict | Lý do |
|----------|---------|-------|
| Tech stack (Next.js + FastAPI + Celery + Supabase) | ✅ 100% | Stack phổ biến, nhiều dev quen |
| Module 0-Lite (auth + credit + RLS) | ✅ 100% | Supabase có sẵn, đã verify |
| Module 1 Discovery | ✅ 95% | Logic rõ, quota budget OK |
| Module 2A Data Collection | ✅ 95% | Batch 50 IDs tối ưu, quota rotation có kế hoạch |
| Module 2B Deterministic Analysis | ✅ 100% | Python thuần, Appendix A formulas rõ |
| Module 2C NLP DNA | ✅ 90% | Cần verify HF model VN, nhưng 3-layer chuẩn |
| Module 3 Script Gen | ✅ 90% | RAG pipeline có trong v2 + Appendix E3 |
| Quota budget | ✅ 95% | 5 keys × 10K = 50K units/day, dư sức |

### 4.2. Rủi ro kỹ thuật cần mitigate

| Rủi ro | Mức độ | Mitigation |
|---------|--------|------------|
| **pytrends bị Google block** | 🟠 Medium | Cache 7 ngày, fallback SerpAPI, UI skip option |
| **Whisper cost cao khi tier-3** | 🟠 Medium | Phân loại credit theo tier thành công |
| **HF emotion model VN chưa verify** | 🟡 Low-Med | Test sớm trong Sprint 2, fallback LLM |
| **PhoBERT trong Worker tốn RAM** | 🟡 Low-Med | Model size ~500MB → cần ≥2GB RAM/worker |
| **Cohere multilingual fallback** | 🟢 Low | Chỉ dùng khi OpenAI fail; cost ~$0.001/call |
| **OpenAI rate limit khi 10 jobs song song** | 🟡 Low-Med | Exponential backoff + request queue |

### 4.3. Cost verification (so với Appendix H)

Giả sử 1 user clone 1 channel + viết 1 script:

| Phase | Cost (PRD v3 ước) | Cost (thực tế review) |
|-------|-------------------|------------------------|
| Module 1 (niche validate) | $0.02 | $0.02 ✓ |
| Deep analysis (13 outputs) | $0.35 | **$0.30** (7 LLM × $0.04 + embed ~$0) |
| 5 transcripts × tier mix 80/20 | $0.09 × 5 | $0.10 (avg) |
| Script gen | $0.055 | $0.055 ✓ |
| Scene breakdown | $0.02 | $0.02 ✓ |
| **Tổng cost** | $0.60 | **~$0.50** |
| **Giá bán** | 185 credits = $1.85 | $1.85 |
| **Margin thực** | 68% | **73%** ✓ |

→ **PRD v3 financially viable**, thậm chí tốt hơn ước tính gốc.

---

## 5. KIẾN NGHỊ THỨ TỰ ƯU TIÊN TRƯỚC KHI CODE

### Bước 1 — BẮT BUỘC (30 phút): Giải quyết 4 điểm Critical A1-A4

| # | Action |
|---|--------|
| A1 | Quyết định: Thumbnail Analysis = output #14 bonus. Update DAG Appendix G và `thumbnail_analysis` column trong bảng đã có sẵn. |
| A2 | Cross-reference: A2 = per-channel, A3 = per-niche. Sửa §12.2 Step 6 thành *"Rank by outlier_strength (see Appendix A2)"*. |
| A3 | Sửa tiêu đề §11.2: "Pipeline (10 steps)" thay vì "7 steps". |
| A4 | Thêm subsection §13.5 "UI Flow" — show progress per output (1/13 → 13/13). |

### Bước 2 — KHUYẾN NGHỊ (1 giờ): Resolve 4 điểm B1-B4

| # | Action |
|---|--------|
| B1 | Thêm §1.1: Lang detection bằng `langdetect` trên 500 chars đầu, cache kết quả trong 24h. |
| B2 | Thêm migration `0010_match_dna_chunks_v2.sql` với `section_filter` parameter. |
| B3 | Phân loại rõ: Phase 1 = 2 layer (in-prompt + regex); Phase 2 thêm LLM validator. Thêm prompt E9. |
| B4 | Thêm "E2.1 Example Output" với Chú Béo case đầy đủ persona + 9-step + 11 mimic rules. |

### Bước 3 — OPTIONAL (30 phút): Decide 5 điểm C1-C5

| # | Action |
|---|--------|
| C1 | Thêm pytrends cache 7 ngày + rate limit (1 req/5s) vào §11.2 Step 8. |
| C2 | Verify `wonrax/phobert-base-vietnamese-emotion` trên HuggingFace Hub, document URL + license trong Appendix F. |
| C3 | Quyết định: Module 1 default = 10 channels, button "Load 10 more" × N, tối đa 100. |
| C4 | Tách credit transcript theo tier: tier-1 = 5 credits, tier-3 (Whisper) = 15 credits. |
| C5 | Phân biệt: Cache YT Data API = TTL 24h (tuân ToS), transcripts = permanent (own processed data). |

---

## 6. CÂU HỎI CẦN USER CHỐT

Trước khi tiến hành code, cần chốt 3 câu hỏi then chốt:

### Q1: Ưu tiên xử lý các điểm mờ thế nào?

- **Option A:** Sửa ngay **4 điểm Critical (A1-A4)** trong PRD → update file → rồi mới code *(an toàn, ~30 phút edit)*
- **Option B:** Sửa luôn **A1-A4 + B1-B4** (~1.5 giờ edit) cho production-ready
- **Option C:** Code trước với assumptions hợp lý, fix các điểm mờ sau *(rủi ro cao nhưng nhanh)*

### Q2: Thumbnail Analysis là #14 bonus hay 1 phần của #8?

- **#14 bonus** *(chạy song song batch 2, cột riêng trong DB — Recommend)*
- **Part of #8 Hook Analysis** *(gộp vào prompt 1)*

### Q3: Bắt đầu code từ Sprint nào?

- **Sprint 1 (Foundation + Module 0-Lite)** — phù hợp nhất nếu muốn chạy được auth + credit trước
- **Sprint 2 (YouTube Collection Engine)** — nếu muốn test quota rotation ngay
- **Sprint 4 end-to-end** — nếu muốn có demo "URL → script" càng sớm càng tốt *(rủi ro: skip foundation)*

---

## 7. KẾT LUẬN

### 7.1. Verdict tổng thể

PRD v3 là một bản tài liệu **rất mạnh** và **gần như production-ready**:

| Tiêu chí | Đánh giá |
|----------|----------|
| Tính chi tiết | ⭐⭐⭐⭐⭐ (5/5) — 9 appendices, 15 formulas, 28 sections |
| Tính nhất quán | ⭐⭐⭐⭐ (4/5) — có 12 điểm mâu thuẫn/nhỏ cần fix |
| Tính khả thi | ⭐⭐⭐⭐ (4/5) — stack chuẩn, có rủi ro cần mitigate |
| Tính ready-for-AI-coding | ⭐⭐⭐⭐ (4/5) — 95% như header cam kết, sau khi fix 4 critical |

### 7.2. Tóm tắt khuyến nghị

**Bắt buộc trước khi code:**
1. Fix **4 điểm Critical** (A1-A4) — ~30 phút
2. Chốt **3 câu hỏi Q1-Q3** ở section 6

**Sau khi code bắt đầu (có thể defer):**
- 4 điểm B1-B4 khi viết prompts
- 5 điểm C1-C5 khi deploy production

### 7.3. Bước tiếp theo được đề xuất

```
┌────────────────────────────────────────────────────────┐
│ Recommended next step                                  │
│                                                        │
│  Edit PRD v3 → fix A1, A2, A3, A4 → commit            │
│       ↓                                                │
│  User chốt Q1 (sửa PRD trước hay code trước?)         │
│       ↓                                                │
│  Nếu "code trước": Assume defaults cho A1, A2, A3, A4  │
│       ↓                                                │
│  Bắt đầu Sprint 1 (Foundation): 2 tuần                │
│   - Monorepo skeleton                                  │
│   - Supabase migrations + RLS                          │
│   - Module 0-Lite (auth + credit + middleware)          │
│   - FastAPI + Celery + Realtime skeleton               │
└────────────────────────────────────────────────────────┘
```

### Default assumptions (nếu "code trước"):
- **A1:** Thumbnail = #14 bonus, DAG update in-line
- **A2:** A2 = per-channel (Deep), A3 = per-niche (Module 1)
- **A3:** Update thành "10 steps"
- **A4:** Show progress bar per output (1/13 → 13/13)

---

## 8. LỊCH SỬ REVIEW

| Phiên bản | Ngày | Reviewer | Ghi chú |
|-----------|------|----------|---------|
| v1 → v2 | 2026-08-04 | Cursor AI | Bổ sung 6 Power Features từ UI screenshot |
| v2 → v3 | 2026-08-05 | Cursor AI | Tổ chức lại PART I-III, 9 Appendix, 15 formulas |
| Review v3 | 2026-08-05 | Cursor AI | File này — 12 điểm mờ |

---

> **File này là ghi chép nghiên cứu** — dùng làm reference khi fix PRD v3 và trong quá trình code.
> Không thay thế PRD v3 chính thức.
