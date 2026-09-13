import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import styles from './Login.module.css';

const DEMOS = [
  { role: 'student',    emoji: '🎓', label: 'Student',        email: 'student@college.edu',    pw: 'Student@123',    route: '/student' },
  { role: 'faculty',    emoji: '👨‍🏫', label: 'Faculty',        email: 'faculty@college.edu',    pw: 'Faculty@123',    route: '/faculty' },
  { role: 'hod',        emoji: '🏛️', label: 'Head of Dept',   email: 'hod@college.edu',        pw: 'HoD@Dept123',    route: '/hod' },
  { role: 'principal',  emoji: '🎩', label: 'Principal',      email: 'principal@college.edu',  pw: 'Principal@123',  route: '/principal' },
  { role: 'university', emoji: '🌐', label: 'University',     email: 'university@keralaedu.in',pw: 'Kerala@Edu2025', route: '/university' },
];

const ROLE_ROUTES = {
  student: '/student', faculty: '/faculty', hod: '/hod', principal: '/principal', university: '/university',
};

export default function Login() {
  const { login, user } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw]     = useState(false);
  const [error, setError]       = useState('');
  const [loading, setLoading]   = useState(false);
  const [activePill, setActivePill] = useState(null);

  // Already logged in redirect
  React.useEffect(() => {
    if (user && user.role) {
      navigate(ROLE_ROUTES[user.role] || '/', { replace: true });
    }
  }, [user, navigate]);

  const fillDemo = (demo) => {
    setEmail(demo.email);
    setPassword(demo.pw);
    setActivePill(demo.role);
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const session = await login(email.trim(), password);
      setLoading(false);
      if (session) {
        navigate(ROLE_ROUTES[session.role] || '/');
      } else {
        setError('Invalid email or password. Try a demo account on the left.');
      }
    } catch (err) {
      setLoading(false);
      setError(err.message || 'Failed to authenticate.');
    }
  };

  return (
    <div className={styles.page}>
      {/* ── Left Panel ── */}
      <div className={styles.left}>
        <div className={styles.leftGrid} />
        <div className={styles.leftOrb} />

        <div className={styles.brand}>
          <div className={styles.brandIcon}>🎓</div>
          <div>
            <div className={styles.brandName}>EduPulse</div>
            <div className={styles.brandSub}>Kerala Higher Education</div>
          </div>
        </div>

        <div className={styles.leftBody}>
          <h1 className={styles.tagline}>
            Feedback that<br /><em>builds futures,</em><br />not fears.
          </h1>
          <p className={styles.taglineSub}>
            Select a role and sign in. Each portal shows only the information relevant to your position.
          </p>

          <div className={styles.demoLabel}>Quick Demo Access</div>
          <div className={styles.demoPills}>
            {DEMOS.map(d => (
              <button
                key={d.role}
                className={`${styles.demoPill} ${activePill === d.role ? styles.demoPillActive : ''}`}
                onClick={() => fillDemo(d)}
                type="button"
              >
                <span className={styles.demoEmoji}>{d.emoji}</span>
                <div className={styles.demoInfo}>
                  <div className={styles.demoRole}>{d.label}</div>
                  <div className={styles.demoCreds}>{d.email}</div>
                </div>
                <span className={styles.demoUse}>USE →</span>
              </button>
            ))}
          </div>
        </div>

        <div className={styles.leftFooter}>
          NAAC SSS Aligned · DPDP Act 2023 Compliant · Non-Punitive by Design
        </div>
      </div>

      {/* ── Right Panel ── */}
      <div className={styles.right}>
        <div className={styles.rightPaper} />

        <div className={styles.formWrap}>
          <h2 className={styles.formTitle}>Welcome back</h2>
          <p className={styles.formSub}>Sign in to your EduPulse portal</p>

          <div className={styles.loginCard}>
            {error && (
              <div className={styles.errorMsg}>⚠️ {error}</div>
            )}

            <form onSubmit={handleSubmit} autoComplete="off">
              <div className={styles.field}>
                <label className={styles.label} htmlFor="email">Email Address</label>
                <input
                  id="email"
                  type="email"
                  className={styles.input}
                  placeholder="your@college.edu"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  required
                />
              </div>

              <div className={styles.field}>
                <label className={styles.label} htmlFor="password">Password</label>
                <div className={styles.inputWrap}>
                  <input
                    id="password"
                    type={showPw ? 'text' : 'password'}
                    className={styles.input}
                    placeholder="••••••••"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    required
                  />
                  <button
                    type="button"
                    className={styles.pwToggle}
                    onClick={() => setShowPw(v => !v)}
                  >
                    {showPw ? '🙈' : '👁️'}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                className={`${styles.submitBtn} ${loading ? styles.loading : ''}`}
                disabled={loading}
              >
                {loading ? '⏳ Signing in…' : 'Sign In to EduPulse →'}
              </button>
            </form>
          </div>

          <div className={styles.backLink}>
            <Link to="/">← Back to home</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
