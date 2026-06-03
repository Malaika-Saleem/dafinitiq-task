import React, { useState } from 'react'

const API = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export default function Auth(){
  const [email,setEmail] = useState('')
  const [name,setName] = useState('')
  const [password,setPassword] = useState('')
  const [otp, setOtp] = useState('')
  const [showOtpModal, setShowOtpModal] = useState(false)
  const [latestOtp, setLatestOtp] = useState('')
  const [message, setMessage] = useState('')

  async function signup(){
    if(!email || !name || !password){ alert('Please fill email, display name and password'); return }
    const res = await fetch(`${API}/api/auth/signup`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,display_name:name,password})})
    const j = await res.json()
    if(!res.ok) return alert('Error: '+JSON.stringify(j))
    setMessage(j.message || 'OTP sent')
    // if backend returned OTP (dev mode), show it in a modal and autofill
    if(j.otp){
      setLatestOtp(j.otp)
      setOtp(j.otp)
      setShowOtpModal(true)
    }
  }

  async function verify(){
    if(!email || !otp){ alert('Provide email and OTP'); return }
    const res = await fetch(`${API}/api/auth/verify-otp`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,otp})})
    const j = await res.json(); if(!res.ok) return alert('Error: '+JSON.stringify(j)); setMessage(j.message || 'verified')
    // auto-login after verify
    await login()
  }

  async function login(){
    if(!email || !password){ alert('Provide email and password'); return }
    const res = await fetch(`${API}/api/auth/login`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password})})
    const j = await res.json()
    if(!res.ok) return alert('Error: '+JSON.stringify(j))
    if(j.access_token){ localStorage.setItem('va_token', j.access_token); setMessage('Logged in') } else setMessage(JSON.stringify(j))
  }

  async function forgotPassword(){
    if(!email){ alert('Enter your registered email'); return }
    const res = await fetch(`${API}/api/auth/forgot-password`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email})})
    const j = await res.json(); if(!res.ok) return alert('Error: '+JSON.stringify(j)); alert(j.message || 'otp_sent')
  }

  async function resetPassword(){
    const new_password = prompt('Enter new password')
    if(!email || !otp || !new_password) return alert('Provide email, OTP and new password via prompt')
    const res = await fetch(`${API}/api/auth/reset-password`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,otp,new_password})})
    const j = await res.json(); if(!res.ok) return alert('Error: '+JSON.stringify(j)); alert(j.message || 'password_reset')
  }

  return (
    <div className="card">
      <h2>Sign up / Login</h2>
      {message && <div style={{padding:8,background:'#eef',marginBottom:8}}>{message}</div>}
      <input placeholder="email" value={email} onChange={e=>setEmail(e.target.value)} />
      <input placeholder="display name" value={name} onChange={e=>setName(e.target.value)} />
      <input placeholder="password" type="password" value={password} onChange={e=>setPassword(e.target.value)} />
      <div style={{display:'flex',gap:8,marginTop:8}}>
        <button onClick={signup} style={{flex:1}}>Sign Up</button>
        <button onClick={login} style={{flex:1}}>Login</button>
      </div>

      <h3 style={{marginTop:12}}>Verify OTP</h3>
      <input placeholder="otp" value={otp} onChange={e=>setOtp(e.target.value)} />
      <button onClick={verify} style={{marginTop:8}}>Verify & Login</button>

      <div style={{marginTop:12}}>
        <h3>Forgot Password</h3>
        <div style={{display:'flex',gap:8}}>
          <button onClick={forgotPassword}>Request OTP</button>
          <button onClick={resetPassword}>Reset Password (use OTP)</button>
        </div>
      </div>

      {showOtpModal && (
        <div style={{position:'fixed',left:0,top:0,right:0,bottom:0,display:'flex',alignItems:'center',justifyContent:'center',background:'rgba(0,0,0,0.4)'}}>
          <div style={{background:'#fff',padding:20,borderRadius:8,minWidth:300}}>
            <h4>OTP for {email}</h4>
            <div style={{fontSize:20,letterSpacing:2,margin:'8px 0'}}>{latestOtp}</div>
            <div style={{display:'flex',gap:8,justifyContent:'flex-end'}}>
              <button onClick={() => { navigator.clipboard?.writeText(latestOtp); setMessage('OTP copied to clipboard'); }}>Copy</button>
              <button onClick={() => { setShowOtpModal(false); }}>Close</button>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}
