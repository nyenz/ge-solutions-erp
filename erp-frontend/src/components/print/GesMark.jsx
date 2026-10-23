// PATH: erp-frontend/src/components/print/GesMark.jsx
// fix227 (David): the GE Solutions logo on printed documents -- the compass mark of the company website (ges-website,
// src/app/icon.svg): a navy disc, an orange ring and an orange compass needle. On the navy band the disc gets a thin
// light edge so the mark stays visible.
import React from 'react';

const GesMark = ({ className = '' }) => (
    <svg className={className} viewBox="0 0 32 32" aria-hidden="true" focusable="false">
        <circle cx="16" cy="16" r="15" fill="#0b2545" stroke="rgba(255,255,255,0.55)" strokeWidth="0.8" />
        <circle cx="16" cy="16" r="11" fill="none" stroke="#ea580c" strokeWidth="2" />
        <path d="M20.5 11.5 17.8 17.8 11.5 20.5 14.2 14.2Z" fill="#ea580c" />
    </svg>
);

export default GesMark;
