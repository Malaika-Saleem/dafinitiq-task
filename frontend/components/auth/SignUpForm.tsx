"use client"
import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { useRouter } from 'next/navigation'

const step1 = z.object({ display_name: z.string().min(1), email: z.string().email(), password: z.string().min(6) })
const step2 = z.object({ otp: z.string().min(1) })

export default function SignUpForm(){
  const [step, setStep] = useState(1)
  const [serverOtp, setServerOtp] = useState('')
  const s1 = useForm({ resolver: zodResolver(step1) })
  const s2 = useForm({ resolver: zodResolver(step2) })
  const [loading,setLoading] = useState(false)
  const router = useRouter()
  const API = process.env.NEXT_PUBLIC_API_BASE || ''

  const submitStep1 = async (data: any) => {
    setLoading(true)
    try{
      const url = API + '/api/auth/signup'
      const res = await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({display_name:data.display_name,email:data.email,password:data.password})})
      const j = await res.json()
      if(!res.ok){ alert(JSON.stringify(j)); return }
      setServerOtp(j.otp || '')
      setStep(2)
    }finally{ setLoading(false) }
  }

  const submitOtp = async (d:any) => {
    setLoading(true)
    try{
      const res = await fetch(API + '/api/auth/verify-otp',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:s1.getValues().email,otp:d.otp})})
      const j = await res.json()
      if(!res.ok){ alert(JSON.stringify(j)); return }
      // account created; redirect to dashboard
      router.push('/dashboard')
    }finally{ setLoading(false) }
  }

  return (
    <div>
      {step===1 && (
        <form onSubmit={s1.handleSubmit(submitStep1)} className="space-y-3">
          <div>
            <label className="text-sm">Display name</label>
            <input className="w-full mt-1 p-2 border rounded" {...s1.register('display_name')} />
          </div>
          <div>
            <label className="text-sm">Email</label>
            <input className="w-full mt-1 p-2 border rounded" {...s1.register('email')} />
          </div>
          <div>
            <label className="text-sm">Password</label>
            <input type="password" className="w-full mt-1 p-2 border rounded" {...s1.register('password')} />
          </div>
          <div>
            <button className="w-full py-2 bg-indigo-600 text-white rounded" disabled={loading}>{loading? 'Sending...' : 'Send Verification Code'}</button>
          </div>
        </form>
      )}
      {step===2 && (
        <form onSubmit={s2.handleSubmit(submitOtp)} className="space-y-3">
          <div>
            <label className="text-sm">OTP Code</label>
            <input className="w-full mt-1 p-2 border rounded" defaultValue={serverOtp} {...s2.register('otp')} />
          </div>
          <div className="flex gap-2">
            <button className="flex-1 py-2 bg-indigo-600 text-white rounded" disabled={loading}>{loading? 'Verifying...' : 'Verify OTP'}</button>
            <button type="button" className="flex-1 py-2 bg-slate-100 rounded" onClick={async ()=>{
              // resend: call signup again with same values
              const v = s1.getValues()
              setLoading(true)
              try{
                const r = await fetch(API + '/api/auth/signup',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({display_name:v.display_name,email:v.email,password:v.password})})
                const jj = await r.json()
                if(!r.ok) alert(JSON.stringify(jj))
                else setServerOtp(jj.otp || '')
              }finally{ setLoading(false) }
            }}>Resend Code</button>
          </div>
        </form>
      )}
    </div>
  )
}
