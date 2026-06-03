import React from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import Auth from './pages/Auth'
import Dashboard from './pages/Dashboard'
import CallDetail from './pages/CallDetail'

export default function App(){
  return (
    <div className="app">
      <header>
        <Link to="/">Auth</Link>
        <Link to="/dashboard">Dashboard</Link>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Auth/>} />
          <Route path="/dashboard" element={<Dashboard/>} />
          <Route path="/dashboard/call/:id" element={<CallDetail/>} />
        </Routes>
      </main>
    </div>
  )
}
