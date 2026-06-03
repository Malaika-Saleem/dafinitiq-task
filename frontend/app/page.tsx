import React from 'react'
import AuthCard from '../components/auth/AuthCard'

export default function Page(){
  return (
    <div className="max-w-6xl w-full grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
      <div className="p-8">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-gradient-to-tr from-indigo-600 to-sky-400 rounded-full flex items-center justify-center text-white font-bold">RV</div>
          <div>
            <h1 className="text-2xl font-semibold">Restaurant Voice AI</h1>
            <p className="text-sm text-slate-500">AI-powered phone ordering for restaurants</p>
          </div>
        </div>
        <ul className="mt-8 space-y-3 text-slate-600">
          <li>• Voice Ordering</li>
          <li>• Drift Detection</li>
          <li>• Order Tracking</li>
          <li>• Staff Dashboard</li>
        </ul>
      </div>
      <div className="p-4">
        <AuthCard />
      </div>
    </div>
  )
}
