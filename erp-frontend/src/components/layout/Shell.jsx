// PATH: erp-frontend/src/components/layout/Shell.jsx
import React, { useState } from 'react';
import Header from './Header';
import Sidebar from './Sidebar';
import styles from './Shell.module.css';

/**
 * GOLDEN SEED — NAVIGATION SHELL
 * Manages sidebar collapsed/expanded state.
 * Passes onToggle to both Header (hamburger) and Sidebar (auto-close on mobile).
 */
const Shell = ({ children }) => {
    const [isCollapsed, setIsCollapsed] = useState(false);
    const location = useLocation();

    // fix48: auto-contract sidebar on Ledger
    useEffect(() => {
        if (location.pathname.includes('/land/projects')) {
            setIsCollapsed(true);
        }
    }, [location.pathname]);


    const handleSidebarToggle = () => setIsCollapsed(prev => !prev);

    return (
        <div className={styles.shell}>
            <Header onToggle={handleSidebarToggle} />

            <div className={styles.mainWrapper}>
                {/*
                  onToggle is passed to Sidebar so it can collapse itself
                  on mobile when the user navigates to a new page — without
                  needing the user to manually press the hamburger again.
                */}
                <Sidebar
                    isCollapsed={isCollapsed}
                    onToggle={handleSidebarToggle}
                />

                <main className={styles.mainContent}>
                    <div className={styles.scrollArea}>
                        {children}
                    </div>
                </main>
            </div>
        </div>
    );
};

export default Shell;