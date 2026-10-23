// PATH: erp-frontend/src/components/print/GesMark.jsx
// fix233 (David): the GE Solutions logo on printed documents -- the REAL GES globe logo of the company website
// (ges-website public/logo-globe.png), inlined into the bundle (?inline) so it is already there when the print opens.
// It sits on a small white disc so the navy "GES" letters stay readable on the navy band. (fix227 drew a compass.)
import React from 'react';
import gesGlobe from '../../assets/brand/ges-globe.png?inline';

export const GES_GLOBE = gesGlobe;

const GesMark = ({ className = '' }) => (
    <span className={className} aria-hidden="true"
          style={{ background: '#ffffff', borderRadius: '50%', padding: '0.6mm', boxSizing: 'border-box', display: 'block' }}>
        <img src={gesGlobe} alt="" style={{ width: '100%', height: '100%', display: 'block' }} />
    </span>
);

export default GesMark;
