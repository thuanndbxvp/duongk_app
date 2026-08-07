# R4-PHASE1-REPORT: Infrastructure Polish

> **Phase**: Round 4 Phase 1 — Infrastructure Polish
> **Date**: 2026-08-07
> **Scope**: Next.js Dockerfile + Docker Compose Healthcheck

---

## MỤC TIÊU

Thực hiện các cải tiến hạ tầng cho production deployment trên VPS Ubuntu 24.04.

---

## THAY ĐỔI 1: Next.js Dockerfile — Sharp Installation

### File: `apps/web/Dockerfile`

**Mục đích:** Bổ sung `sharp` để tối ưu image optimization trong Next.js standalone container.

**Trước:**
```dockerfile
USER nextjs
EXPOSE 3000
ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
```

**Sau:**
```dockerfile
USER nextjs
EXPOSE 3000
ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

# ─── Sharp for image optimization ───
RUN npm install sharp

CMD ["node", "server.js"]
```

**Chi tiết thay đổi:**
- Thêm `RUN npm install sharp` sau khi set USER nextjs
- Sharp được cài đặt ở layer cuối cùng trước CMD để tận dụng Docker layer caching

**Lợi ích:**
- Image optimization hoạt động đúng trong standalone container
- Giảm kích thước ảnh khi serve qua Next.js
- Hỗ trợ WebP/AVIF conversion tự động

---

## THAY ĐỔI 2: Docker Compose — API Healthcheck Timeout

### File: `docker-compose.prod.yml`

**Mục đích:** Tăng healthcheck timeout từ 5s lên 10s để phù hợp với startup time của FastAPI.

**Trước:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-fsS", "http://localhost:8000/health"]
  interval: 30s
  timeout: 5s
  retries: 3
```

**Sau:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-fsS", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

**Chi tiết thay đổi:**
- `timeout: 5s` → `timeout: 10s`

**Lý do:**
- FastAPI startup với 2 workers có thể mất 5-8 giây
- Timeout 5s quá ngắn, gây false positive healthcheck failures
- Timeout 10s đủ thời gian cho application khởi động hoàn chỉnh

---

## XÁC NHẬN: REDIS CONFIGURATION

Theo yêu cầu, Redis configuration được giữ nguyên:

```yaml
# ─── Redis (cache, rate limit - giữ lại cho middleware) ───
redis:
  image: redis:7-alpine
  restart: unless-stopped
  volumes:
    - redis_data:/data
  networks:
    - appnet
```

- ✅ Container `redis` được giữ nguyên
- ✅ Volume `redis_data` được giữ nguyên
- ✅ Network configuration được giữ nguyên
- ✅ Không có thay đổi nào đối với Redis

---

## FILES CHANGED

| File | Thay đổi |
|---|---|
| `apps/web/Dockerfile` | +1 line (`RUN npm install sharp`) |
| `docker-compose.prod.yml` | +1 line (`timeout: 10s`) |

---

## VERIFICATION COMMANDS

Sau khi deploy, chạy các commands sau để verify:

```bash
# 1. Kiểm tra image được build với sharp
docker images | grep web

# 2. Kiểm tra healthcheck hoạt động
docker compose -f docker-compose.prod.yml ps api
# Output mong đợi: "Up (healthy)" sau 30-60 giây

# 3. Test health endpoint trực tiếp
curl http://localhost:8000/health
```

---

## NEXT STEPS

Phase 1 hoàn tất. Các phases tiếp theo:

| Phase | Mô tả | Status |
|---|---|---|
| Phase 1 | Next.js + Healthcheck (file này) | ✅ HOÀN THÀNH |
| Phase 2 | Optional: Dead code cleanup | ⏳ Pending |
| Phase 3 | Optional: Documentation final review | ⏳ Pending |

---

**Trạng thái**: ✅ PHASE 1 COMPLETE
