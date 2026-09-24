import React, { useState, useMemo } from 'react';
import { FiDatabase, FiFilter, FiBarChart2, FiDownload, FiTable } from 'react-icons/fi';
import { CATALOGUE, ENTITIES } from './reportsCatalog';
import styles from './ReportStudio.module.css';

export default function ReportStudio() {
  const [scope, setScope] = useState('PROJECTS');
  const [activeReport, setActiveReport] = useState(null);
  
  const scopeReports = useMemo(() => CATALOGUE.filter(r => r.entity === scope), [scope]);
  
  const handleSelectReport = (report) => {
    setActiveReport(report);
  };

  return (
    <div className={styles.studio}>
      <div className={styles.scopeBar}>
        {ENTITIES.map(e => (
          <button 
            key={e} 
            className={`${styles.scopeBtn} ${scope === e ? styles.scopeBtnActive : ''}`}
            onClick={() => { setScope(e); setActiveReport(null); }}
          >
            {e}
          </button>
        ))}
      </div>

      <div className={styles.catalogue}>
        <h2 className={styles.catalogueTitle}>{scope} REPORTS</h2>
        <div className={styles.catalogueGrid}>
          {scopeReports.map(r => (
            <button 
              key={r.id} 
              className={`${styles.catalogueCard} ${activeReport?.id === r.id ? styles.catalogueCardActive : ''}`}
              onClick={() => handleSelectReport(r)}
            >
              <span className={styles.cardTitle}>{r.name}</span>
              <span className={styles.cardDesc}>{r.desc}</span>
            </button>
          ))}
        </div>
      </div>

      {activeReport && (
        <div className={styles.builderArea}>
          <div className={styles.builderPanel}>
             <h3>BUILDER: {activeReport.name}</h3>
             <p className={styles.builderHint}>Select fields and filters to generate results.</p>
          </div>
          <div className={styles.resultsPanel}>
             <h3>RESULTS</h3>
             <p className={styles.resultsHint}>Chart and table will render here in Stage 3.</p>
          </div>
        </div>
      )}
    </div>
  );
}