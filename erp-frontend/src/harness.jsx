import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { useGlobalTypeAhead } from './components/common/globalTypeAhead';
const App = () => { useGlobalTypeAhead(); const [open, setOpen] = useState(false); const [v, setV] = useState('');
  return (<div data-ta-field><button id="t" onClick={() => setOpen(o => !o)}>SORT {v}</button>
    {open && <div data-ta-list>{['Amount Paid', 'Client', 'Date Paid', 'Deleted Project', 'Kind'].map(x => <button key={x} onClick={() => { setV(x); setOpen(false); }}>{x}</button>)}</div>}
    <input id="i" /></div>); };
createRoot(document.getElementById('root')).render(<App />);
