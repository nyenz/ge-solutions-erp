// PATH: erp-frontend/src/components/layout/Shell.jsx
import React, { useState, useEffect, useRef } from 'react';
import Header from './Header';
import Sidebar from './Sidebar';
import styles from './Shell.module.css';
import { useLocation } from 'react-router-dom';

/**
 * GOLDEN SEED — NAVIGATION SHELL
 * Manages sidebar collapsed/expanded state.
 * Passes onToggle to both Header (hamburger) and Sidebar (auto-close on mobile).
 */
const Shell = ({ children }) => {
    const location = useLocation();
    // fix48: the sidebar starts contracted on the Ledger (it needs the width)
    // fix188: on a phone the menu is a drawer that covers the page, so it starts CLOSED there (it used to open over
    // the page on every first load and had to be tapped away before anything could be typed)
    const [isCollapsed, setIsCollapsed] = useState(() => location.pathname.includes('/land/projects')
        || (typeof window !== 'undefined' && window.innerWidth <= 768));
    const scrollRef = useRef(null);

    // fix182: the Shell now stays on screen between pages (one header, one bell, one sidebar for the whole visit), so a
    // new page starts at the top and the Ledger still contracts the sidebar when you arrive on it.
    const [lastPath, setLastPath] = useState(location.pathname);
    if (lastPath !== location.pathname) {
        setLastPath(location.pathname);
        if (location.pathname.includes('/land/projects') && !isCollapsed) setIsCollapsed(true);
    }
    useEffect(() => {
        if (scrollRef.current) scrollRef.current.scrollTop = 0;
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
                    <div className={styles.scrollArea} ref={scrollRef}>
                        {children}
                    </div>
                </main>
            </div>
        </div>
    );
};

export default Shell;