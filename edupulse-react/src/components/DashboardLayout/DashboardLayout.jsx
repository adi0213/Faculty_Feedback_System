import React, { useState } from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import Sidebar from '../Sidebar/Sidebar';
import styles from './DashboardLayout.module.css';

export default function DashboardLayout({ allowedRoles }) {
  const { user, loading } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  if (loading) return (
    <div className={styles.loader}>
      <div className={styles.loaderSpinner}></div>
    </div>
  );

  if (!user) return <Navigate to="/login" replace />;
  if (allowedRoles && !allowedRoles.includes(user.role)) return <Navigate to="/login" replace />;

  return (
    <div className={styles.layout}>
      <Sidebar mobileOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className={styles.content}>
        {/* Topbar */}
        <header className={styles.topbar}>
          <button className={styles.menuBtn} onClick={() => setSidebarOpen(true)} aria-label="Open menu">
            <span />
            <span />
            <span />
          </button>
          <div className={styles.topbarRight}>
            <span className={styles.termBadge}>Term 2025–S2</span>
          </div>
        </header>

        {/* Page content */}
        <main className={styles.main}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
