import React from 'react'

export default function FilterBar(){
  return (
    <div className="flex flex-col sm:flex-row gap-3 items-center">
      <input placeholder="Search calls" className="p-2 border rounded flex-1" />
      <input type="date" className="p-2 border rounded" />
      <select className="p-2 border rounded">
        <option>All</option>
        <option>Completed</option>
        <option>Pending</option>
        <option>Cancelled</option>
      </select>
    </div>
  )
}
