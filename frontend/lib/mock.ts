export type Call = {
  id: string
  date: string
  duration: string
  caller: string
  status: 'Completed' | 'Pending' | 'Cancelled'
  drift: boolean
  total: string
  start: string
  end: string
  transcript: {role:'user'|'ai', text:string}[]
  order: {name:string,qty:number,price:string}[]
}

export const mockCalls: Call[] = [
  {
    id: 'CALL-001', date: '2026-06-03', duration: '02:14', caller: '555-1234', status: 'Completed', drift:false, total: '$23.50',
    start: '2026-06-03 10:12', end:'2026-06-03 10:14',
    transcript:[{role:'user',text:'Hi I want two margherita pizzas'},{role:'ai',text:'Got it, anything else?'},{role:'user',text:'No thanks'}],
    order:[{name:'Margherita Pizza',qty:2,price:'$22.00'}]
  },
  {
    id: 'CALL-002', date: '2026-06-03', duration: '01:10', caller: '555-9876', status: 'Pending', drift:true, total: '$15.00',
    start: '2026-06-03 11:00', end:'2026-06-03 11:01',
    transcript:[{role:'user',text:'I want a burger please'},{role:'ai',text:'Single or double?'},{role:'user',text:'Single with fries'}],
    order:[{name:'Burger (Single)',qty:1,price:'$10.00'},{name:'Fries',qty:1,price:'$5.00'}]
  }
]

export function mockCallById(id:string){
  return mockCalls.find(c=>c.id===id) || null
}
