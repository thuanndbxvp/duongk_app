import './globals.css';

export const metadata = {
  title: 'AppDK — AI YouTube Script Generator',
  description: 'DNA phong cách kênh YouTube, sinh script viral trong vài phút.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi" className="dark">
      <body className="min-h-dvh text-[15px] leading-relaxed antialiased">
        <div className="app-bg" aria-hidden="true" />
        {children}
      </body>
    </html>
  );
}
