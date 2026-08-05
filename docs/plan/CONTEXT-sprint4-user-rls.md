# Sprint 4 Task Group 1: User & Database Security (RLS)

## 1. Context & Mục đích

### Bối cảnh dự án

**AppDK** là SaaS AI cho YouTube. Sprints 1-3 đã xây Backend Engines nhưng **mock user_id = 'system'** (theo User Review Required trong implementation_plan_v1_fixes §0). Sprint 4 "đóng gói" sản phẩm bằng cách thêm lớp User thật.

### Sprint 4 trong roadmap

```
Sprint 1: Foundation ✅
Sprint 2: Deep Analysis ✅
Sprint 3: AI Script Generation ✅
Sprint 4: User, Auth, Credit & UI ← ĐÂY
├── Task Group 1: User & Database Security ← ĐÂY
├── Task Group 2: Next.js BFF
├── Task Group 3: Credit System
├── Task Group 4: Frontend Dashboard
└── Task Group 5: Integration & E2E
```

### Mục đích task group này

- **Bật Row Level Security (RLS)** cho tất cả tables production
- **Setup Supabase Auth** (email/password)
- **JWT Verify** với `SUPABASE_JWT_SECRET` (D11 FIX - security critical)
- **Migration:** Từ mock user_id sang real user_id qua Supabase Auth

### Môi trường

- **Backend:** Python 3.12 + FastAPI 0.115+ (JWT via PyJWT)
- **Database:** Supabase (PostgreSQL 15 + Row Level Security)
- **Auth:** Supabase Auth (email/password)
- **Dependencies cần check:**
  - `requirements.txt` cần thêm `PyJWT>=2.8.0`
  - Existing tables: `users`, `jobs`, `credit_transactions`, `channel_assistants`, `dna_chunks`, `channel_deep_analysis`, `generated_ideas`, `generated_scripts` (đã tạo ở Sprint 1-3)

---

## 2. Database Schema Changes

### SQL Migration: 0017_enable_rls_policies.sql

Trigger: Đặt team từ `user_id = 'system'` (mock) → `user_id` thật từ JWT.

### Existing users table (Sprint 1)

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  email TEXT UNIQUE NOT NULL,
  full_name TEXT,
  avatar_url TEXT,
  credits INT DEFAULT 0,
  tier TEXT DEFAULT 'free',
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### RLS Policies cần ENABLE

```sql
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE credit_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE channel_assistants ENABLE ROW LEVEL SECURITY;
ALTER TABLE channel_deep_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE dna_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE generated_ideas ENABLE ROW LEVEL SECURITY;
ALTER TABLE generated_scripts ENABLE ROW LEVEL SECURITY;

-- Policy: Users chỉ thấy/xóa/sửa data của chính họ
CREATE POLICY "users_own_data" ON users FOR ALL
  USING (id = auth.uid());

CREATE POLICY "users_own_jobs" ON jobs FOR ALL
  USING (user_id = auth.uid());

CREATE POLICY "users_own_assistants" ON channel_assistants FOR ALL
  USING (user_id = auth.uid());

CREATE POLICY "users_own_credit_tx" ON credit_transactions FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM users u
      WHERE u.id = credit_transactions.user_id
        AND u.id = auth.uid()
    )
  );

-- Channel deep analysis qua assistant
CREATE POLICY "users_own_analysis" ON channel_deep_analysis FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM channel_assistants ca
      WHERE ca.id = channel_deep_analysis.assistant_id
        AND ca.user_id = auth.uid()
    )
  );

-- DNA chunks qua assistant
CREATE POLICY "users_own_chunks" ON dna_chunks FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM channel_assistants ca
      WHERE ca.id = dna_chunks.assistant_id
        AND ca.user_id = auth.uid()
    )
  );

-- Generated ideas qua assistant
CREATE POLICY "users_own_ideas" ON generated_ideas FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM channel_assistants ca
      WHERE ca.id = generated_ideas.assistant_id
        AND ca.user_id = auth.uid()
    )
  );

-- Generated scripts qua assistant
CREATE POLICY "users_own_scripts" ON generated_scripts FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM channel_assistants ca
      WHERE ca.id = generated_scripts.assistant_id
        AND ca.user_id = auth.uid()
    )
  );
```

---

## 3. JWT Authentication (D11 FIX)

### Why critical

Trong Sprints 1-3, pseudocode dùng:
```python
payload = jwt.decode(token, options={'verify_signature': False})  # ← INSECURE
```

Task này fix bằng cách dùng PyJWT với `SUPABASE_JWT_SECRET`.

### Token format

Supabase Auth phát JWT với:
- Algorithm: HS256
- Payload: `{sub: user_id, aud: 'authenticated', exp: ..., email: ..., ...}`
- Secret: `SUPABASE_JWT_SECRET` (lấy từ Supabase Dashboard)

### Files to Create

| File | Purpose |
|------|---------|
| `supabase/migrations/0017_enable_rls_policies.sql` | Enable RLS + Policies |
| `apps/api/dependencies/auth.py` | JWT verify dependency |
| `apps/api/dependencies/auth_test.py` | Unit tests |
| `apps/api/routers/users.py` | User CRUD endpoints |
| `.env.example` (update) | Thêm `SUPABASE_JWT_SECRET` |

---

## 4. Output Expectations

### Khi hoàn thành task group này

1. **RLS enabled** cho tất cả tables
2. **JWT verify** hoạt động đúng với PyJWT
3. **reject invalid tokens** (forge token → 401)
4. **User endpoints** trả về user info dựa trên JWT

### Example

```bash
# Client login → get tokens
POST /auth/v1/token?grant_type=password
Body: {email, password}
↳ Returns: {access_token, refresh_token, user}

# Client gọi API với token
GET /api/users/me
Headers: Authorization: Bearer <access_token>
↳ Returns: {id, email, full_name, credits, tier}
```

---

## 5. Constraints

- **JWT verify PHẢI dùng** `SUPABASE_JWT_SECRET` (không được `verify_signature:False`)
- **Không break** existing tests (Sprints 1-3)
- **Backwards compatible** với assumed `user_id = 'system'` (Tầng 2 sẽ check)
- **Unit test coverage** ≥ 90% cho JWT verify (theo H1 FIX)
