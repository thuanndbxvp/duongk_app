import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="container mx-auto p-8">
      <h1 className="text-4xl font-bold">AppDK</h1>
      <p className="text-gray-600 mt-4">
        AI YouTube Script Generator - Tạo kịch bản YouTube chuẩn phong cách kênh mẫu
      </p>
      <Link href="/login" className="text-blue-600 mt-4 inline-block hover:underline">
        Đăng nhập →
      </Link>
    </main>
  );
}
