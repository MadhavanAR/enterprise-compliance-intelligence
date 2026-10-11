import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: 'Enterprise Compliance Intelligence (ECI) | Auditable RAG Engine',
  description:
    'Document-grounded regulatory compliance Q&A with verifiable citations, fail-closed policy guardrails, and audit transparency.',
  keywords: [
    'compliance',
    'RAG',
    'regulatory',
    'auditing',
    'AI compliance',
    'vector search',
    'grounded generation',
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body>{children}</body>
    </html>
  );
}
