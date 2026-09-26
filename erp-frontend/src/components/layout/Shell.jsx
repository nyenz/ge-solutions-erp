// PATH: erp-frontend/src/components/layout/Shell.jsx
import React, { useState } from 'react';
import Header from './Header';
import Sidebar from './Sidebar';
import styles from './Shell.module.css';
import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

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

    /* The sidebar no longer collapses itself the instant a nav link is
       clicked -- picking a destination should still leave the panel open
       while the new page loads. It's the first click INSIDE the page
       content itself, once you're actually there working the page, that
       clears the panel out of the way. */
    const handleContentClick = () => {
        if (!isCollapsed) setIsCollapsed(true);
    };

    return (
        <div className={styles.shell}>
            <Header onToggle={handleSidebarToggle} />

            <div className={styles.mainWrapper}>
                {/*
                  onToggle is passed to Sidebar purely for its mobile backdrop
                  -- tapping outside the open drawer still closes it right
                  away. Auto-collapse on navigation now lives below instead,
                  on the content area itself (handleContentClick).
                */}
                <Sidebar
                    isCollapsed={isCollapsed}
                    onToggle={handleSidebarToggle}
                />

                <main className={styles.mainContent} onClick={handleContentClick}>
                    <div className={styles.scrollArea}>
                        {children}
                    </div>
                </main>
            </div>
        </div>
    );
};

export default Shell;