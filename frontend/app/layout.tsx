import '../styles/globals.css'
import React from 'react'

export const metadata = {
  title: 'Restaurant Voice AI',
  description: 'AI-powered phone ordering for restaurants',
}

export default function RootLayout({ children }: { children: React.ReactNode }){
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen flex items-center justify-center p-4">
          {children}
        </div>
      </body>
    </html>
  )
}
