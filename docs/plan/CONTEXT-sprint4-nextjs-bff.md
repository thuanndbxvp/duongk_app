# Sprint 4 Task Group 2: Next.js BFF (Backend-For-Frontend)

## 1. Context & Mục đích

### Bối cảnh

Sprint 4.1 đã bật RLS + JWT verify. Sprint 4.2 xây **Next.js BFF** để:
- Frontend không trực tiếp gọi FastAPI
- BFF xử lý auth (cookies), proxy requests với JWT token
- Verify token tại FastAPI (Layer 2 defence)

### Mục đích task group này

- Khởi tạo Next.js 15 (App Router)
- Setup cookie-based session
- Proxy pattern: Frontend → BFF → FastAPI

### Pattern

```
Browser → Next.js Route Handler → FastAPI
   (cookie)      (JavaScript)        (JWT via Bearer)
```

### Dependencies

- ✅ Task 1: JWT auth (đã có)
- ⏳ Task 3: Credit system (depends on BFF)

---

## 2. Tech Stack

- **Next.js 15** (App Router, Server Components)
- **React 19**
- **TypeScript** (strict mode)
- **shadcn/ui + TailwindCSS** (UI - optional trong task này)
- **Cookie session** (HttpOnly, Secure, SameSite=Lax)

---

## 3. File Structure

```
apps/web/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── api/
│   │   ├── auth/
│   │   │   ├── login/route.ts
│   │   │   ├── logout/route.ts
│   │   │   └── callback/route.ts
│   │   ├── scripts/
│   │   │   └── generate/route.ts
│   │   └── jobs/
│   │       └── [id]/route.ts
│   └── (auth)/
│       ├── login/page.tsx
│       └── signup/page.tsx
├── lib/
│   ├── auth.ts
│   ├── api-client.ts
│   └── supabase-client.ts
├── components/
│   ├── auth-form.tsx
│   └── (UI components)
├── package.json
├── tsconfig.json
├── next.config.js
└── tailwind.config.ts
```

---

## 4. Output Expectations

### Khi hoàn thành task group này

1. **Next.js 15** chạy được trên `localhost:3000`
2. **Login page** sử dụng Supabase Auth UI
3. **Route Handler** proxy requests tới FastAPI với JWT
4. **Cookie session** set HttpOnly, Secure

---

## 5. Acceptance Summary

| # | Criteria |
|---|----------|
| AC1 | Next.js 15 init thành công |
| AC2 | Login page works |
| AC3 | Route Handler proxies with JWT |
| AC4 | Cookie session secure |
| AC5 | All tests pass |
