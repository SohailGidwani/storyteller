import type { Metadata, Viewport } from 'next'
import { Lora, Nunito } from 'next/font/google'
import './globals.css'

const lora = Lora({
  subsets: ['latin'],
  variable: '--font-lora',
  display: 'swap',
})

const nunito = Nunito({
  subsets: ['latin'],
  variable: '--font-nunito',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Storyworld',
  description: 'Your personalized storybook',
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${lora.variable} ${nunito.variable} bg-cream min-h-screen font-nunito text-ink antialiased`}>
        {children}
      </body>
    </html>
  )
}
