"use client"
import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { useRouter } from 'next/navigation'

const schema = z.object({ email: z.string().email(), password: z.string().min(1) })

export default function SignInForm(){
  const { register, handleSubmit, formState } = useForm({ resolver: zodResolver(schema) })
  const [loading,setLoading] = useState(false)
  const router = useRouter()
  const API = process.env.NEXT_PUBLIC_API_BASE || ''
  const onSubmit = async (data: any) => {
    setLoading(true)
    const url = API + '/api/auth/login'
    try{
      const res = await fetch(url, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(data) })
      const j = await res.json()
      if(!res.ok){
        alert(j.detail || JSON.stringify(j))
      } else {
        localStorage.setItem('va_token', j.access_token)
        router.push('/dashboard')
      }
    }catch(err:any){
      console.error('Network error', err)
      alert(`Network error contacting ${url}: ${err?.message || err}`)
    }finally{ setLoading(false) }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
      <div>
        <label className="text-sm">Email</label>
        <input className="w-full mt-1 p-2 border rounded" {...register('email')} />
      </div>
      <div>
        <label className="text-sm">Password</label>
        <input type="password" className="w-full mt-1 p-2 border rounded" {...register('password')} />
      </div>
      <div>
        <button className="w-full py-2 bg-indigo-600 text-white rounded" disabled={loading}>{loading? 'Signing in...' : 'Sign In'}</button>
      </div>
    </form>
  )
}
