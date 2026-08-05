import './globals.css';

export const metadata = {
  title: 'AppDK',
  description: 'AI YouTube Script Generator',
};

import { CreditsBadge } from '@/components/credits-badge';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body className="bg-gray-50 min-h-screen">
        <header className="border-b bg-white sticky top-0 z-50">
          <div className="container mx-auto px-8 py-4 flex items-center justify-between">
            <a href="/" className="font-bold text-xl text-blue-600">AppDK</a>
            <CreditsBadge />
          </div>
        </header>
        {children}
      </body>
    </html>
  );
}
