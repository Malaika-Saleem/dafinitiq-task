"use client"
import React, { useState } from 'react'

export default function ForgotForm(){
  const [step,setStep] = useState(1)
  const [email,setEmail] = useState('')
  const [otp,setOtp] = useState('')
  const [newPass,setNewPass] = useState('')
  const [loading,setLoading] = useState(false)
  const API = process.env.NEXT_PUBLIC_API_BASE || ''

  const sendOtp = async () => {
    setLoading(true)
    try{
      const url = API + '/api/auth/forgot-password'
      const res = await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email})})
      const j = await res.json()
      if(!res.ok) return alert(JSON.stringify(j))
      setStep(2)
    }finally{ setLoading(false) }
  }

  const verifyOtp = async () => {
    setLoading(true)
    try{
      const url = API + '/api/auth/verify-otp'
      const res = await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,otp})})
      const j = await res.json()
      if(!res.ok) return alert(JSON.stringify(j))
      setStep(3)
    }finally{ setLoading(false) }
  }

  const reset = async () => {
    setLoading(true)
    try{
      const url = API + '/api/auth/reset-password'
      const res = await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,otp,new_password:newPass})})
      const j = await res.json()
      if(!res.ok) return alert(JSON.stringify(j))
      setStep(4)
    }finally{ setLoading(false) }
  }

  return (
    <div>
      {step===1 && (
        <div className="space-y-3">
          <input placeholder="email" className="w-full p-2 border rounded" value={email} onChange={e=>setEmail(e.target.value)} />
          <button className="w-full py-2 bg-indigo-600 text-white rounded" onClick={sendOtp}>Send OTP</button>
        </div>
      )}
      {step===2 && (
        <div className="space-y-3">
          <input placeholder="otp" className="w-full p-2 border rounded" value={otp} onChange={e=>setOtp(e.target.value)} />
          <button className="w-full py-2 bg-indigo-600 text-white rounded" onClick={verifyOtp}>Verify OTP</button>
        </div>
      )}
      {step===3 && (
        <div className="space-y-3">
          <input placeholder="new password" type="password" className="w-full p-2 border rounded" value={newPass} onChange={e=>setNewPass(e.target.value)} />
          <button className="w-full py-2 bg-indigo-600 text-white rounded" onClick={reset}>Reset Password</button>
        </div>
      )}
      {step===4 && (
        <div className="p-4 bg-green-50 rounded">Password reset complete. You may now sign in.</div>
      )}
    </div>
  )
}
