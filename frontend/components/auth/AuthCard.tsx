"use client"
import React, { useState } from 'react'
import SignInForm from './SignInForm'
import SignUpForm from './SignUpForm'
import ForgotForm from './ForgotForm'

export default function AuthCard(){
  const [tab, setTab] = useState<'signin'|'signup'|'forgot'>('signin')
  return (
    <div className="card max-w-md mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Welcome back</h3>
        <div className="text-sm text-slate-500">Secure access</div>
      </div>
      <div className="flex gap-2 mb-4">
        <button onClick={()=>setTab('signin')} className={`flex-1 py-2 rounded ${tab==='signin' ? 'bg-slate-100' : ''}`}>Sign In</button>
        <button onClick={()=>setTab('signup')} className={`flex-1 py-2 rounded ${tab==='signup' ? 'bg-slate-100' : ''}`}>Sign Up</button>
        <button onClick={()=>setTab('forgot')} className={`flex-1 py-2 rounded ${tab==='forgot' ? 'bg-slate-100' : ''}`}>Forgot</button>
      </div>

      <div>
        {tab==='signin' && <SignInForm />}
        {tab==='signup' && <SignUpForm />}
        {tab==='forgot' && <ForgotForm />}
      </div>
    </div>
  )
}
