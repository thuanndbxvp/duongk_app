import Link from 'next/link';
import { IconSparkle, IconBrain, IconChannels, IconDashboard, IconPlus } from '@/components/icons';

const features = [
  {
    icon: IconChannels,
    title: 'DNA phong cách kênh',
    desc: 'Phân tích transcript, phong cách mở bài, hook và cấu trúc kênh mẫu để tái sử dụng.',
  },
  {
    icon: IconBrain,
    title: 'Sinh script viral',
    desc: 'Tạo kịch bản YouTube chuẩn phong cách kênh trong vài phút với AI pipeline.',
  },
  {
    icon: IconSparkle,
    title: 'An toàn & riêng tư',
    desc: 'Dữ liệu của bạn được mã hoá và xử lý cô lập theo từng project.',
  },
];

const steps = [
  { num: '01', title: 'Tạo dự án', desc: 'Chọn kênh mẫu và phong cách bạn muốn bắt chước.' },
  { num: '02', title: 'AI phân tích DNA', desc: 'Hệ thống phân tích transcript, hook, nhịp nội dung.' },
  { num: '03', title: 'Sinh & chỉnh sửa', desc: 'Nhận kịch bản hoàn chỉnh, tinh chỉnh rồi xuất bản.' },
];

export default function HomePage() {
  return (
    <main className="min-h-dvh">
      {/* Top nav */}
      <header className="sticky top-0 z-40 backdrop-blur-xl bg-[rgba(7,6,13,0.6)] border-b border-[var(--glass-border)]">
        <div className="max-w-6xl mx-auto flex items-center justify-between px-6 h-16">
          <Link href="/" className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg gradient-bg grid place-items-center text-white font-bold">
              A
            </div>
            <span className="font-semibold tracking-tight">AppDK</span>
          </Link>
          <nav className="hidden md:flex items-center gap-6 text-sm text-[var(--fg-secondary)]">
            <a href="#features" className="hover:text-[var(--fg-primary)] transition">Tính năng</a>
            <a href="#how" className="hover:text-[var(--fg-primary)] transition">Cách hoạt động</a>
            <Link href="/pricing" className="hover:text-[var(--fg-primary)] transition">Bảng giá</Link>
          </nav>
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="hidden sm:inline-flex h-9 px-4 items-center text-sm font-medium text-[var(--fg-secondary)] hover:text-[var(--fg-primary)] transition"
            >
              Đăng nhập
            </Link>
            <Link
              href="/login?signup=1"
              className="inline-flex h-9 px-4 items-center rounded-lg text-sm font-semibold glass border border-[var(--glass-border-strong)] text-[var(--brand-300)] hover:bg-[var(--surface-hover)] hover:text-white transition"
            >
              Đăng ký miễn phí
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div
          aria-hidden
          className="pointer-events-none absolute -top-40 left-1/2 -translate-x-1/2 h-[480px] w-[480px] rounded-full bg-[var(--brand-500)] opacity-25 blur-[120px]"
        />
        <div className="relative max-w-6xl mx-auto px-6 pt-24 pb-20 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass text-xs font-medium text-[var(--brand-300)]">
            <IconSparkle size={14} /> AI YouTube Script Generator
          </div>
          <h1 className="mt-6 text-4xl md:text-6xl font-bold tracking-tight">
            <span className="gradient-text">DNA phong cách kênh YouTube</span>
            <br />
            <span className="text-[var(--fg-primary)]">sinh script viral trong vài phút</span>
          </h1>
          <p className="mt-6 text-lg text-[var(--fg-secondary)] max-w-2xl mx-auto">
            AppDK phân tích transcript, hook và cấu trúc kênh mẫu — sau đó tạo kịch bản
            chuẩn phong cách bạn muốn bắt chước.
          </p>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
            <Link
              href="/login?signup=1"
              className="inline-flex items-center gap-2 px-6 h-12 rounded-xl text-sm font-semibold glass border border-[var(--glass-border-strong)] text-[var(--brand-300)] hover:bg-[var(--surface-hover)] hover:text-white transition"
            >
              <IconPlus size={16} /> Bắt đầu miễn phí
            </Link>
            <Link
              href="/pricing"
              className="inline-flex items-center gap-2 px-6 h-12 rounded-xl text-sm font-medium text-[var(--fg-primary)] glass hover:bg-[var(--surface-hover)] transition"
            >
              Xem bảng giá
            </Link>
          </div>
          <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto">
            {[
              { k: '10x', v: 'nhanh hơn viết tay' },
              { k: '4', v: 'modules AI' },
              { k: '99%', v: 'Uptime' },
              { k: '24/7', v: 'Pipeline chạy nền' },
            ].map((s) => (
              <div key={s.k} className="glass rounded-2xl p-4 text-left">
                <div className="text-2xl font-bold gradient-text">{s.k}</div>
                <div className="text-xs text-[var(--fg-secondary)] mt-1">{s.v}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="relative max-w-6xl mx-auto px-6 py-20">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass text-xs font-medium text-[var(--brand-300)]">
            <IconDashboard size={14} /> Tính năng
          </div>
          <h2 className="mt-4 text-3xl md:text-4xl font-bold tracking-tight">
            Mọi thứ bạn cần để <span className="gradient-text">tái tạo phong cách</span>
          </h2>
        </div>
        <div className="grid md:grid-cols-3 gap-4">
          {features.map((f) => (
            <div key={f.title} className="relative overflow-hidden rounded-3xl glass-strong p-6">
              <div
                aria-hidden
                className="pointer-events-none absolute -top-16 -right-16 h-40 w-40 rounded-full bg-[var(--brand-500)] opacity-15 blur-3xl"
              />
              <div className="relative h-10 w-10 rounded-xl gradient-bg grid place-items-center text-white">
                <f.icon size={18} />
              </div>
              <h3 className="relative mt-5 text-lg font-semibold">{f.title}</h3>
              <p className="relative mt-2 text-sm text-[var(--fg-secondary)] leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="relative max-w-6xl mx-auto px-6 py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
            Cách hoạt động — <span className="gradient-text">3 bước</span>
          </h2>
        </div>
        <div className="grid md:grid-cols-3 gap-4">
          {steps.map((s) => (
            <div key={s.num} className="rounded-3xl glass p-6">
              <div className="text-sm font-mono text-[var(--brand-400)]">{s.num}</div>
              <h3 className="mt-2 text-lg font-semibold">{s.title}</h3>
              <p className="mt-2 text-sm text-[var(--fg-secondary)] leading-relaxed">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="relative max-w-6xl mx-auto px-6 py-20">
        <div className="relative overflow-hidden rounded-3xl glass-strong p-12 text-center">
          <div
            aria-hidden
            className="pointer-events-none absolute -top-24 left-1/2 -translate-x-1/2 h-72 w-72 rounded-full bg-[var(--brand-500)] opacity-25 blur-3xl"
          />
          <h2 className="relative text-3xl md:text-4xl font-bold tracking-tight">
            Sẵn sàng tạo <span className="gradient-text">script viral</span> đầu tiên?
          </h2>
          <p className="relative mt-4 text-[var(--fg-secondary)] max-w-xl mx-auto">
            Đăng ký miễn phí, tạo dự án đầu tiên và để AppDK làm phần còn lại.
          </p>
          <Link
            href="/login?signup=1"
            className="relative inline-flex items-center gap-2 px-6 h-12 rounded-xl text-sm font-semibold text-white gradient-bg shadow-[var(--shadow-glow)] hover:opacity-90 transition mt-8"
          >
            <IconSparkle size={16} /> Đăng ký miễn phí
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[var(--glass-border)]">
        <div className="max-w-6xl mx-auto px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-[var(--fg-secondary)]">
          <div>© {new Date().getFullYear()} AppDK. All rights reserved.</div>
          <div className="flex items-center gap-6">
            <Link href="/pricing" className="hover:text-[var(--fg-primary)] transition">Bảng giá</Link>
            <Link href="/login" className="hover:text-[var(--fg-primary)] transition">Đăng nhập</Link>
          </div>
        </div>
      </footer>
    </main>
  );
}
