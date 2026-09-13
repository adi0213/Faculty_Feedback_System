import React from 'react';
import styles from './Card.module.css';

export function Card({ children, variant = 'default', className = '', style = {}, hover = true }) {
  return (
    <div
      className={`${styles.card} ${styles[variant]} ${hover ? styles.hoverable : ''} ${className}`}
      style={style}
    >
      {children}
    </div>
  );
}

export function CardHeader({ title, icon, action, className = '' }) {
  return (
    <div className={`${styles.header} ${className}`}>
      <div className={styles.headerLeft}>
        {icon && <span className={styles.headerIcon}>{icon}</span>}
        <span className={styles.headerTitle}>{title}</span>
      </div>
      {action && <div className={styles.headerAction}>{action}</div>}
    </div>
  );
}
