import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import styles from './Sidebar.module.css';

const ROLE_NAVS = {
  student:    [{ icon: '📋', label: 'Submit Feedback', to: '/student' }],
  faculty:    [
    { icon: '📊', label: 'Overview',                  to: '/faculty' },
    { icon: '🔍', label: 'Transparency & Development', to: '/faculty/transparency' },
  ],
  hod:        [
    { icon: '📊', label: 'Overview',          to: '/hod' },
    { icon: '👥', label: 'Faculty Roster',    to: '/hod/roster' },
    { icon: '⚠️', label: 'Flags & Alerts',   to: '/hod/flags' },
  ],
  principal:  [
    { icon: '🏫', label: 'College Overview',  to: '/principal' },
    { icon: '📊', label: 'Dept Compare',      to: '/principal/compare' },
  ],
  university: [
    { icon: '🌐', label: 'System Overview',   to: '/university' },
    { icon: '🏫', label: 'College Onboarding',to: '/university/colleges' },
    { icon: '📈', label: 'FDP Outcomes',      to: '/university/fdp' },
  ],
};

const ROLE_META = {
  student:    { label: 'Student',          emoji: '🎓' },
  faculty:    { label: 'Faculty',          emoji: '👨‍🏫' },
  hod:        { label: 'Head of Dept.',    emoji: '🏛️' },
  principal:  { label: 'Principal',        emoji: '🎩' },
  university: { label: 'University Auth.', emoji: '🌐' },
};

export default function Sidebar({ mobileOpen, onClose }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  if (!user) return null;

  const navItems = ROLE_NAVS[user.role] || [];
  const roleMeta = ROLE_META[user.role] || {};
  const initials = user.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <>
      {/* Mobile overlay */}
      {mobileOpen && <div className={styles.overlay} onClick={onClose} />}

      <aside className={`${styles.sidebar} ${mobileOpen ? styles.open : ''}`}>
        {/* Logo */}
        <div className={styles.logo}>
          <div className={styles.logoMark}>🎓</div>
          <div>
            <div className={styles.logoName}>EduPulse</div>
            <div className={styles.logoSub}>Kerala Higher Education</div>
          </div>
        </div>

        {/* Navigation */}
        <nav className={styles.nav}>
          <div className={styles.navSection}>MY PORTAL</div>
          {navItems.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to.split('/').length <= 2}
              className={({ isActive }) =>
                `${styles.navItem} ${isActive ? styles.active : ''}`
              }
              onClick={onClose}
            >
              <span className={styles.navIcon}>{item.icon}</span>
              <span className={styles.navLabel}>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* User Footer */}
        <div className={styles.footer}>
          <div className={styles.userPill}>
            <div className={styles.avatar}>{initials}</div>
            <div className={styles.userInfo}>
              <div className={styles.userName}>{user.name.split(' ').slice(0, 2).join(' ')}</div>
              <div className={styles.userRole}>{roleMeta.emoji} {roleMeta.label}</div>
            </div>
          </div>
          <button className={styles.logoutBtn} onClick={handleLogout}>
            Sign Out
          </button>
        </div>
      </aside>
    </>
  );
}
