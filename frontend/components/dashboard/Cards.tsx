import React from 'react'

function Card({title, value, icon}:{title:string,value:string,icon?:React.ReactNode}){
  return (
    <div className="bg-white p-4 rounded shadow flex items-center justify-between">
      <div>
        <div className="text-sm text-slate-500">{title}</div>
        <div className="text-2xl font-semibold">{value}</div>
      </div>
      <div className="text-slate-400">{icon}</div>
    </div>
  )
}

export default function DashboardCards(){
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card title="Total Calls" value="1,234" />
      <Card title="Orders Today" value="128" />
      <Card title="Drift Events" value="3" />
      <Card title="Revenue" value="$4,320" />
    </div>
  )
}
