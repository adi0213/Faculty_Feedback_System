import React, { useMemo, useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { DB } from '../../data/db';
import { compositeScore, scoreToBand, generateSuggestions } from '../../data/advisor';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend
} from 'recharts';
import styles from './FacultyDashboard.module.css';
import EvaluationTransparency from './EvaluationTransparency';

const DIMS = ['clarity','punctuality','fairness','approachability','methodology','pacing','engagement','practical','assessment','overall'];
const DIM_LABELS = { clarity:'Clarity', punctuality:'Punctuality', fairness:'Fairness', approachability:'Approachable', methodology:'Methodology', pacing:'Pacing', engagement:'Engagement', practical:'Practical', assessment:'Assessment', overall:'Overall' };

/* ── Composite Score Hero Ring ── */
function CompositeScoreHero({ avg, band, fac, deptAvg }) {
  const pct = (avg / 5);
  const R = 68; const CX = 84; const CY = 84; const stroke = 10;
  const circumference = 2 * Math.PI * R;
  const dashOffset = circumference * (1 - pct);

  const hasDeptAvg  = deptAvg !== null && deptAvg !== undefined;
  const myVsDept    = hasDeptAvg ? (avg - deptAvg).toFixed(1) : null;
  const isUp        = myVsDept !== null && myVsDept >= 0;

  // Get top 3 highest and lowest scoring dims
  const dimEntries = DIMS
    .filter(d => fac.scores[d] != null && fac.scores[d] > 0)
    .map(d => ({ dim: d, score: fac.scores[d] }));
  const sorted  = [...dimEntries].sort((a, b) => b.score - a.score);
  const topDims = sorted.slice(0, 3);
  const lowDims = sorted.slice(-Math.min(3, sorted.length)).reverse().filter(
    d => !topDims.includes(d)
  ).slice(0, 3);

  const ringColor = avg >= 4 ? '#1E9E68' : avg >= 3 ? '#C9954A' : '#C94A4A';
  const ringTrack = avg >= 4 ? 'rgba(30,158,104,.12)' : avg >= 3 ? 'rgba(201,149,74,.12)' : 'rgba(201,74,74,.12)';

  return (
    <div className={styles.heroCard}>
      <div className={styles.heroGlow} style={{ background: `radial-gradient(ellipse 60% 80% at 0% 50%, ${ringColor}18, transparent)` }} />

      {/* Left: Ring */}
      <div className={styles.heroRingWrap}>
        <svg width={CX * 2} height={CY * 2} style={{ display: 'block' }}>
          <circle cx={CX} cy={CY} r={R} fill="none" stroke={ringTrack} strokeWidth={stroke} />
          <circle
            cx={CX} cy={CY} r={R} fill="none" stroke={ringColor} strokeWidth={stroke}
            strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={dashOffset}
            transform={`rotate(-90 ${CX} ${CY})`}
            style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(.25,.46,.45,.94)' }}
          />
          <text x={CX} y={CY - 8} textAnchor="middle" fill={ringColor}
            style={{ fontFamily: "'Playfair Display', serif", fontSize: 30, fontWeight: 700 }}>
            {avg}
          </text>
          <text x={CX} y={CY + 14} textAnchor="middle" fill="#8A9E99"
            style={{ fontSize: 12, fontWeight: 600 }}>
            out of 5
          </text>
        </svg>
        <div className={`${styles.heroRingBand} ${styles[`band_${band.cls}`]}`}>
          {band.icon} {band.band}
        </div>
      </div>

      {/* Right: Details */}
      <div className={styles.heroDetails}>
        <div className={styles.heroHeadline}>
          <div className={styles.heroTitle}>Composite Score</div>
          <div className={styles.heroTerm}>
            {fac.responses} student responses
            {fac.term ? ` · ${fac.term}` : ''}
          </div>
        </div>

        {/* Vs Dept */}
        <div className={styles.heroDeptRow}>
          <div className={styles.heroDeptItem}>
            <div className={styles.heroDeptLabel}>Your Score</div>
            <div className={styles.heroDeptValue} style={{ color: ringColor }}>{avg}</div>
          </div>
          <div className={styles.heroDeptDivider} />
          <div className={styles.heroDeptItem}>
            <div className={styles.heroDeptLabel}>Dept. Average</div>
            <div className={styles.heroDeptValue} style={{ color: hasDeptAvg ? undefined : '#8A9E99' }}>
              {hasDeptAvg ? deptAvg : <span style={{ fontSize: '1rem' }}>N/A</span>}
            </div>
          </div>
          <div className={styles.heroDeptDivider} />
          <div className={styles.heroDeptItem}>
            <div className={styles.heroDeptLabel}>vs Department</div>
            {myVsDept !== null ? (
              <div className={styles.heroDeptValue} style={{ color: isUp ? '#1E9E68' : '#C94A4A', fontSize: '1.4rem' }}>
                {isUp ? '+' : ''}{myVsDept}
              </div>
            ) : (
              <div className={styles.heroDeptValue} style={{ color: '#8A9E99', fontSize: '1rem' }}>N/A</div>
            )}
          </div>
        </div>

        {/* Dimension highlights */}
        <div className={styles.heroDimSection}>
          <div className={styles.heroDimGroup}>
            <div className={styles.heroDimGroupLabel}>💪 Strengths</div>
            <div className={styles.heroDimPills}>
              {topDims.map(({ dim, score }) => (
                <span key={dim} className={`${styles.heroDimPill} ${styles.heroDimPillGood}`}>
                  {DIM_LABELS[dim]} <strong>{score.toFixed(1)}</strong>
                </span>
              ))}
            </div>
          </div>
          <div className={styles.heroDimGroup}>
            <div className={styles.heroDimGroupLabel}>📈 Growth Areas</div>
            <div className={styles.heroDimPills}>
              {lowDims.map(({ dim, score }) => (
                <span key={dim} className={`${styles.heroDimPill} ${styles.heroDimPillWeak}`}>
                  {DIM_LABELS[dim]} <strong>{score.toFixed(1)}</strong>
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function DimBar({ dim, score }) {
  const pct   = (score / 5) * 100;
  const color = score >= 4 ? '#1E6F4A' : score >= 3 ? '#C9954A' : '#9A3C2C';
  return (
    <div className={styles.dimBar}>
      <div className={styles.dimBarHeader}>
        <span className={styles.dimBarLabel}>{DIM_LABELS[dim]}</span>
        <span className={styles.dimBarScore} style={{ color }}>{score.toFixed(1)}</span>
      </div>
      <div className={styles.dimBarTrack}>
        <div
          className={styles.dimBarFill}
          style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${color}cc, ${color})` }}
        />
      </div>
    </div>
  );
}

function WeekCard({ week, idx, defaultOpen, completedTasks, onToggleTask }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className={styles.weekCard}>
      <button className={styles.weekHeader} onClick={() => setOpen(v => !v)}>
        <div className={styles.weekNum}>{idx + 1}</div>
        <div className={styles.weekInfo}>
          <div className={styles.weekTitle}>{week.week}</div>
          <div className={styles.weekPhase}>{week.phase}</div>
        </div>
        <span className={`${styles.weekChev} ${open ? styles.weekChevOpen : ''}`}>▶</span>
      </button>
      {open && (
        <div className={styles.weekBody}>
          {week.tasks.map((t, i) => {
            const taskId = `${week.week}_${i}`;
            const isDone = !!completedTasks[taskId];
            return (
              <div
                key={i}
                className={`${styles.weekTask} ${isDone ? styles.weekTaskDone : ''}`}
                onClick={() => onToggleTask(taskId)}
                style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 10 }}
              >
                <input
                  type="checkbox"
                  checked={isDone}
                  onChange={() => {}}
                  style={{ accentColor: '#1E6F4A', width: 16, height: 16, cursor: 'pointer' }}
                />
                <span style={{ textDecoration: isDone ? 'line-through' : 'none', opacity: isDone ? 0.65 : 1 }}>
                  {t}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ── Dashboard Overview ────────────────────────────────────────────────────────
function OverviewTab({ fac, deptAvg, onGoToTransparency }) {
  const avg       = fac.composite ?? compositeScore(fac.scores);
  const band      = scoreToBand(avg);
  const sugg      = generateSuggestions(fac);
  const [completedTasks, setCompletedTasks] = useState({});

  const handleToggleTask = (taskId) => {
    setCompletedTasks(prev => ({ ...prev, [taskId]: !prev[taskId] }));
  };

  const totalTasks = useMemo(() => {
    if (!sugg.taskPlan) return 0;
    return sugg.taskPlan.weeks.reduce((acc, w) => acc + w.tasks.length, 0);
  }, [sugg.taskPlan]);

  const doneCount = useMemo(() => {
    return Object.values(completedTasks).filter(Boolean).length;
  }, [completedTasks]);

  const progressPct = totalTasks > 0 ? Math.round((doneCount / totalTasks) * 100) : 0;

  const top3Courses = useMemo(() => {
    return (sugg.courses || []).slice(0, 3);
  }, [sugg.courses]);

  const trendData = fac.trend && fac.trend.length > 0
    ? fac.trend
    : [{ term: fac.term || '2025-S2', score: avg }];

  const deptAvgVal = deptAvg != null ? deptAvg : null;

  // Only show dimensions that have actual scores
  const activeDims = DIMS.filter(d => (fac.scores[d] || 0) > 0);
  const activeRadarData = activeDims.map(d => ({
    dim: DIM_LABELS[d],
    mine: fac.scores[d] || 0,
    ...(deptAvgVal !== null ? { dept: deptAvgVal } : {}),
  }));

  return (
    <div className={styles.bento}>

      {/* ── 1. Composite Score Hero ── full-width */}
      <div className={styles.span12}>
        <CompositeScoreHero avg={avg} band={band} fac={fac} deptAvg={deptAvgVal} />
      </div>

      {/* ── 2. Dimension Bars + Score Trend ── side by side */}
      <div className={`${styles.card} ${styles.span6}`}>
        <div className={styles.cardHeader}>
          <div className={styles.cardTitle}>📐 Dimension Scores</div>
          <span className={styles.mono}>{activeDims.length} rated</span>
        </div>
        {activeDims.length > 0
          ? activeDims.map(d => <DimBar key={d} dim={d} score={fac.scores[d]} />)
          : <div style={{ color: '#8A9E99', fontSize: 13, padding: '12px 0' }}>No dimension scores yet — awaiting student feedback.</div>
        }
      </div>

      <div className={`${styles.card} ${styles.span6}`}>
        <div className={styles.cardHeader}>
          <div className={styles.cardTitle}>📈 Score Trend</div>
          <span className={styles.mono}>Last 4 terms</span>
        </div>
        <ResponsiveContainer width="100%" height={activeDims.length > 5 ? 200 : 170}>
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(13,31,30,.06)" />
            <XAxis dataKey="term" tick={{ fontSize: 10, fill: '#8A9E99' }} axisLine={false} tickLine={false} />
            <YAxis domain={[1,5]} tick={{ fontSize: 10, fill: '#8A9E99' }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{ background: '#FDFAF4', border: '1px solid rgba(13,31,30,.1)', borderRadius: 10, fontSize: 12 }}
              itemStyle={{ color: '#2E6B60' }}
            />
            <Line type="monotone" dataKey="score" stroke="#2E6B60" strokeWidth={2.5}
              dot={{ r: 4, fill: '#2E6B60', strokeWidth: 2, stroke: '#fff' }} />
          </LineChart>
        </ResponsiveContainer>

        {/* Radar — compact, inside the trend card when dims exist */}
        {activeDims.length > 0 && (
          <>
            <div className={styles.cardHeader} style={{ marginTop: 16, paddingTop: 14, borderTop: '1px solid rgba(13,31,30,.06)', borderBottom: 'none', marginBottom: 0, paddingBottom: 0 }}>
              <div className={styles.cardTitle}>🎯 Profile vs Dept Avg</div>
            </div>
            <ResponsiveContainer width="100%" height={210}>
              <RadarChart data={activeRadarData}>
                <PolarGrid stroke="rgba(13,31,30,.07)" />
                <PolarAngleAxis dataKey="dim" tick={{ fontSize: 10, fill: '#4A5E5A' }} />
                <Radar name="My Score" dataKey="mine" stroke="#2E6B60" fill="rgba(46,107,96,.15)" strokeWidth={2} />
                <Radar name="Dept Avg"  dataKey="dept" stroke="#9C9387" fill="rgba(156,147,135,.07)" strokeWidth={1.5} strokeDasharray="4 4" />
                <Legend iconSize={10} wrapperStyle={{ fontSize: 10 }} />
              </RadarChart>
            </ResponsiveContainer>
          </>
        )}
      </div>

      {/* ── 3. Improvement Plan OR Good Performance ── */}
      {sugg.needsImprovement ? (
        <>
          {/* Recommended Courses */}
          {top3Courses.length > 0 && (
            <div className={`${styles.card} ${styles.span12}`}>
              <div className={styles.cardHeader}>
                <div>
                  <div className={styles.cardTitle}>🎓 Recommended Development Courses</div>
                  <div style={{ fontSize: 11.5, color: '#8A9E99', marginTop: 3 }}>
                    Matched to your growth areas: <strong style={{ color: '#9C7423' }}>{sugg.weakDims.map(d => DIM_LABELS[d] || d).join(', ')}</strong>
                  </div>
                </div>
                <span className={styles.badge} style={{ background:'rgba(201,149,74,.12)', color:'#9C7423', border:'1px solid rgba(201,149,74,.2)' }}>
                  AI Matched
                </span>
              </div>
              <div className={styles.coursesGrid}>
                {top3Courses.map((c, i) => (
                  <div key={i} className={styles.courseCard}>
                    <div className={styles.courseProvider}>{c.provider}</div>
                    <div className={styles.courseName}>{c.name}</div>
                    <div className={styles.courseMeta}>{c.institution} · {c.duration}</div>
                    <div className={styles.courseMatch}>🎯 {c.match}</div>
                    <div style={{ marginTop: 12, display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                      <a
                        href={c.url || '#'}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ padding: '5px 12px', background: 'rgba(46,107,96,0.08)', borderRadius: 8, fontSize: 12, textDecoration: 'none', color: '#2E6B60', fontWeight: 700, border: '1px solid rgba(46,107,96,.15)' }}
                      >
                        Open Course →
                      </a>
                      <button
                        onClick={onGoToTransparency}
                        style={{ padding: '5px 12px', background: 'transparent', border: '1px solid rgba(13,31,30,0.15)', borderRadius: 8, fontSize: 12, color: '#4A5E5A', cursor: 'pointer', fontWeight: 600 }}
                      >
                        📤 Upload Certificate
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 4-Week Improvement Plan */}
          {sugg.taskPlan && (
            <div className={`${styles.card} ${styles.span12}`}>
              <div className={styles.cardHeader} style={{ flexWrap: 'wrap', gap: 10 }}>
                <div>
                  <div className={styles.cardTitle}>✅ 4-Week Improvement Plan</div>
                  <div style={{ fontSize: 12, color: '#4A5E5A', marginTop: 3, lineHeight: 1.5 }}>
                    🤖 {sugg.message}
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: '#1E6F4A' }}>
                    {progressPct}% ({doneCount}/{totalTasks})
                  </div>
                  <span className={styles.badge} style={{ background:'rgba(74,144,136,.1)', color:'#2E6B60', border:'1px solid rgba(74,144,136,.18)' }}>
                    {sugg.taskPlan.title}
                  </span>
                </div>
              </div>
              <div style={{ height: 5, background: 'rgba(13,31,30,0.06)', borderRadius: 3, margin: '4px 0 16px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${progressPct}%`, background: 'linear-gradient(90deg, #1E6F4A, #2E9E68)', transition: 'width 0.3s ease' }} />
              </div>
              <div className={styles.weekAccordion}>
                {sugg.taskPlan.weeks.map((week, idx) => (
                  <WeekCard
                    key={idx}
                    week={week}
                    idx={idx}
                    defaultOpen={idx === 0}
                    completedTasks={completedTasks}
                    onToggleTask={handleToggleTask}
                  />
                ))}
              </div>
            </div>
          )}
        </>
      ) : (
        <div className={`${styles.card} ${styles.span12}`}>
          <div className={styles.goodPerf}>
            <div className={styles.goodIcon}>🌟</div>
            <div className={styles.goodTitle}>Outstanding Performance!</div>
            <div className={styles.goodSub}>{sugg.message}</div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function FacultyDashboard() {
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [fac, setFac]           = useState(null);
  const [deptAvg, setDeptAvg]   = useState(null);
  const [loading, setLoading]   = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    const TERM = '2025-S2';
    async function load() {
      setLoading(true);
      try {
        // 1. Fetch own dashboard (richest data — scores, trend, band, etc.)
        const dash = await DB.getMyFacultyDashboard(TERM);
        if (dash) {
          const dimObj = dash.dimension_scores || {};
          const trendArr = (dash.score_trend || []).map(t => ({
            term: t.term || t.composite_score,
            score: typeof t.composite_score === 'number' ? +t.composite_score.toFixed(2) : null,
          })).filter(t => t.score !== null);

          setFac({
            id: dash.id,
            user_id: dash.user_id || user.id,
            name: dash.name,
            code: dash.faculty_code || dash.code,
            dept: dash.dept,
            subject: dash.subject || 'General',
            college: dash.college,
            responses: dash.current_responses ?? dash.response_count ?? 0,
            composite: typeof dash.composite_score === 'number'
              ? +dash.composite_score.toFixed(2)
              : null,
            band: dash.score_band,
            scores: typeof dimObj === 'object' ? dimObj : {},
            trend: trendArr,
            weakDims: dash.weak_dimensions || [],
            strongDims: dash.strong_dimensions || [],
            isKAnonymityMet: dash.is_k_anonymity_met ?? true,
            kThreshold: dash.k_anonymity_threshold ?? 5,
            term: TERM,
          });

          // 2. Fetch dept analytics for real dept avg
          if (dash.college && dash.dept) {
            const deptData = await DB.getDepartmentAnalytics(dash.college, dash.dept);
            if (Array.isArray(deptData) && deptData.length > 0) {
              const d = deptData[0];
              const avg = d.avg_composite ?? d.average_composite ?? null;
              setDeptAvg(avg !== null ? +parseFloat(avg).toFixed(2) : null);
            }
          }
        } else {
          // Fallback: faculty list
          const list = await DB.getAllFaculties();
          const me = list.find(f => f.user_id === user.id || f.id === user.id) || list[0];
          if (me) {
            setFac({
              ...me,
              composite: me.composite ?? null,
              trend: (me.trend || []).map((s, i) => ({ term: `Term ${i+1}`, score: s })),
              weakDims: [],
              strongDims: [],
              isKAnonymityMet: true,
              kThreshold: 5,
              term: TERM,
            });
          }
        }
      } catch (e) {
        console.error('FacultyDashboard load error:', e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [user.id]);

  // Sync route with active tab
  useEffect(() => {
    if (location.pathname.includes('transparency')) {
      setActiveTab('transparency');
    } else {
      setActiveTab('overview');
    }
  }, [location.pathname]);

  const handleTabSwitch = (tabKey) => {
    setActiveTab(tabKey);
    if (tabKey === 'transparency') {
      navigate('/faculty/transparency');
    } else {
      navigate('/faculty');
    }
  };

  if (loading) return (
    <div style={{ padding: 60, textAlign: 'center', color: '#8A9E99', fontFamily: 'inherit' }}>
      <div style={{ fontSize: 28, marginBottom: 12 }}>⏳</div>
      <div style={{ fontSize: 14 }}>Loading your dashboard…</div>
    </div>
  );
  if (!fac) return (
    <div style={{ padding: 60, textAlign: 'center', color: '#9A3C2C', fontFamily: 'inherit' }}>
      <div style={{ fontSize: 28, marginBottom: 12 }}>⚠️</div>
      <div style={{ fontSize: 14 }}>Faculty profile not found. Please contact admin.</div>
    </div>
  );

  return (
    <div>
      {/* Page header */}
      <div className={styles.pageHeader}>
        <div className={styles.breadcrumb}>👨‍🏫 Faculty Portal</div>
        <h1 className={styles.pageTitle}>{fac.name}</h1>
        <p className={styles.pageSub}>{fac.code} · {fac.subject} · {fac.college}</p>
      </div>

      {/* Main tab bar */}
      <div className={styles.mainTabBar}>
        <button
          id="faculty-tab-overview"
          className={`${styles.mainTab} ${activeTab === 'overview' ? styles.mainTabActive : ''}`}
          onClick={() => handleTabSwitch('overview')}
        >
          📊 Overview
        </button>
        <button
          id="faculty-tab-transparency"
          className={`${styles.mainTab} ${activeTab === 'transparency' ? styles.mainTabActive : ''}`}
          onClick={() => handleTabSwitch('transparency')}
        >
          🔍 Transparency & Development
        </button>
      </div>

      {/* Tab content */}
      {activeTab === 'overview' && (
        <OverviewTab fac={fac} deptAvg={deptAvg} onGoToTransparency={() => handleTabSwitch('transparency')} />
      )}
      {activeTab === 'transparency' && (
        <EvaluationTransparency facultyProfileId={fac.id} />
      )}
    </div>
  );
}
