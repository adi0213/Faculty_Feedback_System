import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, BarChart, Bar, Cell,
  RadarChart, Radar, PolarGrid, PolarAngleAxis
} from 'recharts';
import { DB } from '../../data/db';
import styles from './EvaluationTransparency.module.css';

// ── Verified Course Catalog ──────────────────────────────────────────────────
const COURSE_CATALOG = {
  clarity: [
    { provider: 'Coursera',  name: 'Speak English Professionally: In Person, Online & On the Phone', institution: 'Georgia Tech', duration: '16h', url: 'https://www.coursera.org/learn/speak-english-professionally', match: 'Communication Clarity' },
    { provider: 'NPTEL',     name: 'Effective Engineering Teaching in Practice',                       institution: 'IIT Bombay',   duration: '12 weeks', url: 'https://nptel.ac.in/courses/122104015', match: 'Pedagogical Clarity' },
    { provider: 'MIT OCW',   name: 'Becoming a more versatile learner',                               institution: 'MIT',          duration: 'Self-paced', url: 'https://ocw.mit.edu', match: 'Teaching Clarity' },
  ],
  methodology: [
    { provider: 'Coursera',  name: 'Foundations of Teaching for Learning: Being a Teacher',           institution: 'Commonwealth Edu. Trust', duration: '20h', url: 'https://www.coursera.org/learn/teaching', match: 'Teaching Methods' },
    { provider: 'NPTEL',     name: 'Pedagogy for Online Teaching',                                    institution: 'IIT Madras',    duration: '8 weeks', url: 'https://nptel.ac.in/courses/122106086', match: 'Methodology Diversity' },
    { provider: 'edX',       name: 'Science of Learning: What Every Teacher Should Know',             institution: 'Columbia Univ.', duration: '6 weeks', url: 'https://www.edx.org/course/science-of-learning', match: 'Evidence-Based Teaching' },
  ],
  punctuality: [
    { provider: 'Coursera',  name: 'Work Smarter, Not Harder: Time Management for Personal & Professional Productivity', institution: 'UC Irvine', duration: '6h', url: 'https://www.coursera.org/learn/work-smarter-not-harder', match: 'Time Management' },
    { provider: 'LinkedIn',  name: 'Time Management Fundamentals',                                    institution: 'LinkedIn Learning', duration: '3h', url: 'https://www.linkedin.com/learning/time-management-fundamentals', match: 'Schedule Adherence' },
  ],
  fairness: [
    { provider: 'Coursera',  name: 'Assessment for Learning',                                         institution: 'Univ. of London', duration: '10h', url: 'https://www.coursera.org/learn/assessment-for-learning', match: 'Fair Assessment Design' },
    { provider: 'NPTEL',     name: 'Designing Learner-Centric MOOCs',                                 institution: 'IIT Bombay',   duration: '8 weeks', url: 'https://nptel.ac.in/courses/122104016', match: 'Transparent Evaluation' },
    { provider: 'edX',       name: 'Inclusive Teaching: Supporting All Students in the College Classroom', institution: 'Columbia Univ.', duration: '4 weeks', url: 'https://www.edx.org/course/inclusive-teaching', match: 'Assessment Equity' },
  ],
  approachability: [
    { provider: 'Coursera',  name: 'Inspiring and Motivating Individuals',                            institution: 'Univ. of Michigan', duration: '8h', url: 'https://www.coursera.org/learn/motivate-people-teams', match: 'Student Motivation' },
    { provider: 'LinkedIn',  name: 'Coaching and Mentoring',                                          institution: 'LinkedIn Learning', duration: '4h', url: 'https://www.linkedin.com/learning/coaching-and-mentoring', match: 'Mentoring Skills' },
  ],
  pacing: [
    { provider: 'Coursera',  name: 'Learning How to Learn: Powerful mental tools to help you master tough subjects', institution: 'UC San Diego', duration: '15h', url: 'https://www.coursera.org/learn/learning-how-to-learn', match: 'Cognitive Load & Pacing' },
    { provider: 'NPTEL',     name: 'Curriculum Design',                                               institution: 'IIT Kanpur',   duration: '6 weeks', url: 'https://nptel.ac.in/courses/122104014', match: 'Curriculum Planning' },
  ],
  engagement: [
    { provider: 'Coursera',  name: 'Active Learning in STEM: Motivating and Engaging Students',       institution: 'MIT MITx',     duration: '8h', url: 'https://www.edx.org/course/active-learning-in-stem', match: 'Active Learning' },
    { provider: 'NPTEL',     name: 'Developing Soft Skills and Personality',                          institution: 'IIT Kanpur',   duration: '12 weeks', url: 'https://nptel.ac.in/courses/109104092', match: 'Engagement Skills' },
    { provider: 'Coursera',  name: 'The Science of Well-Being',                                       institution: 'Yale',         duration: '19h', url: 'https://www.coursera.org/learn/the-science-of-well-being', match: 'Classroom Energy' },
  ],
};

// ── Helper: score → band label ───────────────────────────────────────────────
function scoreToBandLabel(score) {
  if (!score) return null;
  if (score >= 4.0) return 'strong';
  if (score >= 3.0) return 'developing';
  return 'needs';
}

// ── Tab button ───────────────────────────────────────────────────────────────
function Tab({ id, label, icon, active, onClick }) {
  return (
    <button
      className={`${styles.tab} ${active ? styles.tabActive : ''}`}
      onClick={() => onClick(id)}
      id={`transparency-tab-${id}`}
    >
      <span className={styles.tabIcon}>{icon}</span>
      <span>{label}</span>
    </button>
  );
}

// ── Score bar ────────────────────────────────────────────────────────────────
function ScoreBar({ score, max = 5 }) {
  const pct = (score / max) * 100;
  const band = scoreToBandLabel(score);
  const colors = { strong: '#1E6F4A', developing: '#C9954A', needs: '#9A3C2C' };
  const color = colors[band] || '#8A9E99';
  return (
    <div className={styles.scoreBarWrap}>
      <div className={styles.scoreBarTrack}>
        <div
          className={styles.scoreBarFill}
          style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${color}bb, ${color})` }}
        />
        {[1, 2, 3, 4, 5].map(n => (
          <div key={n} className={styles.scoreBarTick} style={{ left: `${(n / 5) * 100}%` }} />
        ))}
      </div>
      <span className={styles.scoreBarVal} style={{ color }}>{score.toFixed(1)}</span>
    </div>
  );
}

// ── Questionnaire Tab ─────────────────────────────────────────────────────────
function QuestionnaireTab({ methodology }) {
  const [expanded, setExpanded] = useState(null);
  if (!methodology) return <div className={styles.loading}>Loading questionnaire…</div>;

  return (
    <div className={styles.tabContent}>
      {/* Scoring formula card */}
      <div className={styles.formulaCard}>
        <div className={styles.formulaHeader}>
          <span className={styles.formulaIcon}>🧮</span>
          <div>
            <div className={styles.formulaTitle}>Score Calculation Formula</div>
            <code className={styles.formulaCode}>{methodology.scoring_scale.formula}</code>
          </div>
        </div>
        <p className={styles.formulaDesc}>{methodology.scoring_scale.description}</p>
        <div className={styles.scaleRow}>
          {[1, 2, 3, 4].map(v => (
            <div key={v} className={styles.scaleChip}>
              <div className={styles.scaleRaw}>{v}</div>
              <div className={styles.scaleArrow}>→</div>
              <div className={styles.scaleNorm}>{((v - 1) / 3 * 4 + 1).toFixed(2)}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Weight chart + bands */}
      <div className={styles.twoCol}>
        {/* Dimension weights */}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <div className={styles.cardTitle}>📊 Dimension Weights</div>
          </div>
          <div className={styles.weightList}>
            {methodology.dimensions.map(dim => (
              <div key={dim.id} className={styles.weightRow}>
                <div className={styles.weightMeta}>
                  <span className={styles.weightIcon}>{dim.icon}</span>
                  <span className={styles.weightLabel}>{dim.label}</span>
                </div>
                <div className={styles.weightBar}>
                  <div
                    className={styles.weightFill}
                    style={{ width: `${dim.weight * 100 / 0.2 * 100}%` }}
                  />
                </div>
                <span className={styles.weightPct}>{dim.weight_pct}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Score bands */}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <div className={styles.cardTitle}>🎖️ Score Bands</div>
          </div>
          <div className={styles.bandList}>
            {methodology.score_bands.map(b => (
              <div key={b.band} className={styles.bandRow} style={{ borderLeftColor: b.color }}>
                <div className={styles.bandRange} style={{ color: b.color }}>{b.min.toFixed(1)}–{b.max.toFixed(1)}</div>
                <div>
                  <div className={styles.bandName} style={{ color: b.color }}>{b.band}</div>
                  <div className={styles.bandDesc}>{b.description}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Questions accordion */}
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.cardTitle}>📋 All Evaluation Questions</div>
          <span className={styles.badge}>10 Questions · 7 Dimensions</span>
        </div>
        <div className={styles.qList}>
          {methodology.dimensions.map((dim, idx) => (
            <div key={dim.id} className={styles.qGroup}>
              <button
                className={`${styles.qGroupHeader} ${expanded === dim.id ? styles.qGroupOpen : ''}`}
                onClick={() => setExpanded(expanded === dim.id ? null : dim.id)}
                id={`q-group-${dim.id}`}
              >
                <div className={styles.qGroupLeft}>
                  <span className={styles.qNum}>{idx + 1}</span>
                  <span className={styles.qGroupIcon}>{dim.icon}</span>
                  <div>
                    <div className={styles.qGroupLabel}>{dim.label}</div>
                    <div className={styles.qGroupMeta}>Weight: {dim.weight_pct} · {dim.description}</div>
                  </div>
                </div>
                <span className={`${styles.qChev} ${expanded === dim.id ? styles.qChevOpen : ''}`}>▶</span>
              </button>
              {expanded === dim.id && (
                <div className={styles.qGroupBody}>
                  {dim.questions.map(q => (
                    <div key={q.id} className={styles.qCard}>
                      <div className={styles.qText}>{q.text}</div>
                      <div className={styles.optGrid}>
                        {q.options.map(opt => (
                          <div key={opt.value} className={styles.optCard}>
                            <div className={styles.optVal}>{opt.value}</div>
                            <div className={styles.optLabel}>{opt.label}</div>
                            <div className={styles.optDesc}>{opt.desc}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Sub-question policy */}
      <div className={styles.infoCard}>
        <span className={styles.infoIcon}>ℹ️</span>
        <div>
          <strong>Sub-Questions Policy:</strong> {methodology.sub_question_policy}
        </div>
      </div>
    </div>
  );
}

// ── My Results Tab ────────────────────────────────────────────────────────────
function MyResultsTab({ data, completions, totalBoost, adjustedScore }) {
  if (!data) return <div className={styles.loading}>Loading your results…</div>;

  if (!data.k_anonymity_met) {
    return (
      <div className={styles.tabContent}>
        <div className={styles.thresholdCard}>
          <div className={styles.thresholdIcon}>🔒</div>
          <div className={styles.thresholdTitle}>Anonymity Threshold Not Met</div>
          <p className={styles.thresholdDesc}>
            Your individual scores are currently hidden because only{' '}
            <strong>{data.response_count}</strong> out of{' '}
            <strong>{data.k_anonymity_threshold}</strong> minimum responses required
            have been collected for this term.
          </p>
          <p className={styles.thresholdDesc}>
            This is to protect student anonymity. Scores will be revealed once
            {' '}<strong>{data.k_anonymity_threshold - data.response_count} more student(s)</strong> submit feedback.
          </p>
          <div className={styles.thresholdProgress}>
            <div className={styles.thresholdTrack}>
              <div
                className={styles.thresholdFill}
                style={{ width: `${Math.min(100, (data.response_count / data.k_anonymity_threshold) * 100)}%` }}
              />
            </div>
            <span>{data.response_count} / {data.k_anonymity_threshold} responses</span>
          </div>
        </div>
      </div>
    );
  }

  const bandColors = { strong: '#1E6F4A', developing: '#C9954A', needs: '#9A3C2C' };
  const band = data.score_band || '';
  const bandColor = bandColors[band] || '#4A9088';

  // Radar data
  const radarData = (data.dimensions || []).map(d => ({
    dim: d.label.replace('Teaching ', '').replace(' Fairness', 'Fairness'),
    score: d.score || 0,
  }));

  return (
    <div className={styles.tabContent}>
      {/* Overview row */}
      <div className={styles.overviewRow}>
        <div className={styles.compositeCard}>
          <div className={styles.compositeLabel}>Composite Score</div>
          <div className={styles.compositeVal} style={{ color: bandColor }}>{data.composite_score?.toFixed(2) || '—'}</div>
          <div className={styles.compositeSub}>out of 5.00</div>
          <div className={styles.bandChip} style={{ background: `${bandColor}18`, color: bandColor, borderColor: `${bandColor}33` }}>
            {band === 'strong' ? '🌟 Strong Performer' : band === 'developing' ? '📈 Developing' : '🔧 Needs Improvement'}
          </div>
        </div>
        <div className={styles.radarWrap}>
          <ResponsiveContainer width="100%" height={220}>
            <RadarChart data={radarData} margin={{ top: 10, right: 20, left: 20, bottom: 10 }}>
              <PolarGrid stroke="rgba(13,31,30,.08)" />
              <PolarAngleAxis dataKey="dim" tick={{ fontSize: 10, fill: '#4A5E5A' }} />
              <Radar name="My Score" dataKey="score" stroke={bandColor} fill={`${bandColor}18`} strokeWidth={2} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Development Bonus Row */}
      {totalBoost > 0 && (
        <div className={styles.devBonusRow}>
          <div className={styles.devBonusLeft}>
            <span className={styles.devBonusIcon}>🎓</span>
            <div>
              <div className={styles.devBonusLabel}>Development Bonus</div>
              <div className={styles.devBonusDesc}>{(completions || []).length} course{(completions || []).length !== 1 ? 's' : ''} completed</div>
            </div>
          </div>
          <div className={styles.devBonusRight}>
            <span className={styles.devBonusVal}>+{totalBoost.toFixed(2)}</span>
            {adjustedScore && (
              <span className={styles.devAdjusted}>Adjusted: <strong>{adjustedScore.toFixed(2)}</strong> / 5.00</span>
            )}
          </div>
        </div>
      )}

      {/* Strengths */}
      {data.strengths?.length > 0 && (
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <div className={styles.cardTitle}>✅ Strengths</div>
            <span className={styles.badge} style={{ background: 'rgba(30,111,74,.1)', color: '#1E6F4A' }}>
              {data.strengths.length} strong {data.strengths.length === 1 ? 'area' : 'areas'}
            </span>
          </div>
          <div className={styles.strengthGrid}>
            {data.strengths.map(d => (
              <div key={d.id} className={`${styles.dimCard} ${styles.dimCardStrong}`}>
                <div className={styles.dimCardHeader}>
                  <span className={styles.dimCardIcon}>{d.icon}</span>
                  <div>
                    <div className={styles.dimCardLabel}>{d.label}</div>
                    <div className={styles.dimCardWeight}>{d.weight_pct} of score</div>
                  </div>
                  <div className={styles.dimCardScore} style={{ color: '#1E6F4A' }}>{d.score?.toFixed(1)}</div>
                </div>
                <ScoreBar score={d.score} />
                {d.interpretation && (
                  <p className={styles.dimInterpretation}>{d.interpretation}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Improvement areas */}
      {data.improvement_areas?.length > 0 && (
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <div className={styles.cardTitle}>🔧 Areas for Improvement</div>
            <span className={styles.badge} style={{ background: 'rgba(154,60,44,.08)', color: '#9A3C2C' }}>
              {data.improvement_areas.length} {data.improvement_areas.length === 1 ? 'area' : 'areas'} to develop
            </span>
          </div>
          <div className={styles.strengthGrid}>
            {data.improvement_areas.map(d => (
              <div key={d.id} className={`${styles.dimCard} ${styles.dimCardNeeds}`}>
                <div className={styles.dimCardHeader}>
                  <span className={styles.dimCardIcon}>{d.icon}</span>
                  <div>
                    <div className={styles.dimCardLabel}>{d.label}</div>
                    <div className={styles.dimCardWeight}>{d.weight_pct} of score</div>
                  </div>
                  <div className={styles.dimCardScore} style={{ color: '#9A3C2C' }}>{d.score?.toFixed(1)}</div>
                </div>
                <ScoreBar score={d.score} />
                {d.interpretation && (
                  <p className={styles.dimInterpretation}>{d.interpretation}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All dimensions */}
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.cardTitle}>📐 All Dimensions</div>
        </div>
        <div className={styles.allDims}>
          {(data.dimensions || []).map(d => {
            const band = scoreToBandLabel(d.score);
            const colors = { strong: '#1E6F4A', developing: '#C9954A', needs: '#9A3C2C' };
            const color = colors[band] || '#8A9E99';
            return (
              <div key={d.id} className={styles.allDimRow}>
                <span className={styles.allDimIcon}>{d.icon}</span>
                <div className={styles.allDimInfo}>
                  <div className={styles.allDimLabel}>{d.label}</div>
                  <div className={styles.allDimWeight}>{d.weight_pct}</div>
                </div>
                <div className={styles.allDimBar}>
                  <div className={styles.allDimTrack}>
                    <div
                      className={styles.allDimFill}
                      style={{ width: `${((d.score || 0) / 5) * 100}%`, background: color }}
                    />
                  </div>
                </div>
                <span className={styles.allDimScore} style={{ color }}>{d.score?.toFixed(1) || '—'}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Anonymity assurance */}
      <div className={styles.privacyCard}>
        <div className={styles.privacyHeader}>🔒 Privacy Assurance</div>
        <ul className={styles.privacyList}>
          <li>Scores shown are aggregated across <strong>{data.response_count}</strong> anonymous student responses.</li>
          <li>No individual student response is identifiable in these results.</li>
          <li>Only your own results are visible to you — not other faculty members' scores.</li>
        </ul>
      </div>
    </div>
  );
}

// ── History Tab ───────────────────────────────────────────────────────────────
function HistoryTab({ data }) {
  if (!data) return <div className={styles.loading}>Loading history…</div>;

  const trend = data.score_trend || [];

  if (!trend.length) {
    return (
      <div className={styles.tabContent}>
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>📈</div>
          <div className={styles.emptyTitle}>No Historical Data Yet</div>
          <p className={styles.emptyDesc}>Term-over-term trends will appear here once multiple evaluation cycles have been completed.</p>
        </div>
      </div>
    );
  }

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
      <div className={styles.chartTooltip}>
        <div className={styles.tooltipTerm}>{label}</div>
        {payload.map(p => (
          <div key={p.dataKey} className={styles.tooltipRow} style={{ color: p.color }}>
            {p.name}: <strong>{typeof p.value === 'number' ? p.value.toFixed(2) : p.value}</strong>
          </div>
        ))}
      </div>
    );
  };

  // Calculate deltas
  const firstScore = trend[0]?.composite_score;
  const lastScore = trend[trend.length - 1]?.composite_score;
  const delta = lastScore != null && firstScore != null ? (lastScore - firstScore).toFixed(2) : null;
  const improving = delta > 0;

  return (
    <div className={styles.tabContent}>
      {/* Summary KPIs */}
      <div className={styles.historyKpis}>
        <div className={styles.historyKpi}>
          <div className={styles.historyKpiLabel}>Latest Score</div>
          <div className={styles.historyKpiVal}>{lastScore?.toFixed(2) ?? '—'}</div>
        </div>
        <div className={styles.historyKpi}>
          <div className={styles.historyKpiLabel}>Terms Tracked</div>
          <div className={styles.historyKpiVal}>{trend.length}</div>
        </div>
        {delta !== null && (
          <div className={styles.historyKpi}>
            <div className={styles.historyKpiLabel}>Overall Trend</div>
            <div className={styles.historyKpiVal} style={{ color: improving ? '#1E6F4A' : delta < 0 ? '#9A3C2C' : '#8A9E99' }}>
              {improving ? '↑' : delta < 0 ? '↓' : '→'} {Math.abs(delta)}
            </div>
          </div>
        )}
        <div className={styles.historyKpi}>
          <div className={styles.historyKpiLabel}>Total Responses</div>
          <div className={styles.historyKpiVal}>
            {trend.reduce((s, t) => s + (t.response_count || 0), 0)}
          </div>
        </div>
      </div>

      {/* Trend line chart */}
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.cardTitle}>📈 Composite Score Trend</div>
          <span className={styles.mono}>{trend[0]?.term} – {trend[trend.length - 1]?.term}</span>
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={trend} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(13,31,30,.06)" />
            <XAxis dataKey="term" tick={{ fontSize: 11, fill: '#8A9E99' }} axisLine={false} tickLine={false} />
            <YAxis domain={[1, 5]} tick={{ fontSize: 11, fill: '#8A9E99' }} axisLine={false} tickLine={false} />
            <ReferenceLine y={4.0} stroke="#1E6F4A" strokeDasharray="4 3" strokeOpacity={0.4} label={{ value: 'Strong', position: 'insideRight', fontSize: 10, fill: '#1E6F4A' }} />
            <ReferenceLine y={3.0} stroke="#C9954A" strokeDasharray="4 3" strokeOpacity={0.4} label={{ value: 'Developing', position: 'insideRight', fontSize: 10, fill: '#C9954A' }} />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="composite_score"
              name="Composite Score"
              stroke="#2E6B60"
              strokeWidth={2.5}
              dot={{ r: 5, fill: '#2E6B60', stroke: '#fff', strokeWidth: 2 }}
              activeDot={{ r: 7 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Response count bar chart */}
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.cardTitle}>👥 Response Count per Term</div>
        </div>
        <ResponsiveContainer width="100%" height={160}>
          <BarChart data={trend} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(13,31,30,.06)" vertical={false} />
            <XAxis dataKey="term" tick={{ fontSize: 11, fill: '#8A9E99' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: '#8A9E99' }} axisLine={false} tickLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="response_count" name="Responses" radius={[6, 6, 0, 0]}>
              {trend.map((t, i) => (
                <Cell key={i} fill={t.response_count >= 5 ? '#2E6B60' : '#C9954A'} fillOpacity={0.75} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <p className={styles.chartNote}>
          🟢 Green bars indicate terms with sufficient responses (≥5). 🟡 Amber bars indicate below-threshold terms where scores are hidden.
        </p>
      </div>

      {/* Term breakdown table */}
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.cardTitle}>📅 Term-by-Term Breakdown</div>
        </div>
        <div className={styles.tableWrap}>
          <table>
            <thead>
              <tr>
                <th>Term</th>
                <th>Composite Score</th>
                <th>Responses</th>
                <th>Band</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {trend.map((t, i) => {
                const band = scoreToBandLabel(t.composite_score);
                const bandColors = { strong: '#1E6F4A', developing: '#C9954A', needs: '#9A3C2C' };
                const color = bandColors[band];
                const prevScore = trend[i - 1]?.composite_score;
                const delta = prevScore != null ? (t.composite_score - prevScore).toFixed(2) : null;
                return (
                  <tr key={t.term}>
                    <td><span className={styles.mono}>{t.term}</span></td>
                    <td>
                      <span style={{ color, fontWeight: 700, fontFamily: "'JetBrains Mono', monospace" }}>
                        {t.composite_score?.toFixed(2) ?? '—'}
                      </span>
                      {delta !== null && (
                        <span style={{ marginLeft: 6, fontSize: 11, color: delta > 0 ? '#1E6F4A' : delta < 0 ? '#9A3C2C' : '#8A9E99' }}>
                          ({delta > 0 ? '+' : ''}{delta})
                        </span>
                      )}
                    </td>
                    <td>{t.response_count ?? '—'}</td>
                    <td><span style={{ color, fontWeight: 600, fontSize: 12 }}>{band === 'strong' ? 'Strong' : band === 'developing' ? 'Developing' : 'Needs Improvement'}</span></td>
                    <td>
                      <span className={styles.statusChip} style={{ background: (t.response_count || 0) >= 5 ? 'rgba(30,111,74,.1)' : 'rgba(201,149,74,.1)', color: (t.response_count || 0) >= 5 ? '#1E6F4A' : '#9C7423' }}>
                        {(t.response_count || 0) >= 5 ? '✓ Visible' : '⚠ Hidden'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ── Upload Panel (inline per card) ────────────────────────────────────────────
function UploadPanel({ courseKey, courseName, provider, dimId, onSuccess, onCancel }) {
  const fileRef = useRef();
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('idle'); // idle | uploading | done | error
  const [errorMsg, setErrorMsg] = useState('');

  const handleFileChange = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    const allowed = ['application/pdf','image/jpeg','image/png','image/webp'];
    if (!allowed.includes(f.type) && !f.name.match(/\.(pdf|jpg|jpeg|png|webp)$/i)) {
      setErrorMsg('Only PDF, JPG, PNG or WEBP files are accepted.');
      return;
    }
    if (f.size > 10 * 1024 * 1024) { setErrorMsg('File must be under 10 MB.'); return; }
    setErrorMsg('');
    setFile(f);
  };

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();
    if (!file) { setErrorMsg('Please select a certificate file.'); return; }
    setStatus('uploading');
    try {
      const result = await DB.uploadCertificate({ courseKey, courseName, provider, dimensionId: dimId, file });
      setStatus('done');
      setTimeout(() => onSuccess(result), 600);
    } catch (err) {
      setStatus('error');
      setErrorMsg(err.message || 'Upload failed. Please try again.');
    }
  }, [file, courseKey, courseName, provider, dimId, onSuccess]);

  return (
    <div className={styles.uploadPanel}>
      <div className={styles.uploadPanelTitle}>📤 Upload Completion Certificate</div>
      <p className={styles.uploadPanelDesc}>PDF, JPG, PNG or WEBP · Max 10 MB</p>
      {status === 'done' ? (
        <div className={styles.uploadSuccess}>✅ Certificate uploaded! Marking as completed…</div>
      ) : (
        <form onSubmit={handleSubmit} className={styles.uploadForm}>
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.jpg,.jpeg,.png,.webp"
            onChange={handleFileChange}
            className={styles.uploadInput}
            id={`upload-${courseKey}`}
          />
          <label htmlFor={`upload-${courseKey}`} className={styles.uploadLabel}>
            {file ? `📄 ${file.name}` : '📁 Choose File'}
          </label>
          {errorMsg && <div className={styles.uploadError}>{errorMsg}</div>}
          <div className={styles.uploadActions}>
            <button
              type="submit"
              className={styles.uploadSubmitBtn}
              disabled={status === 'uploading' || !file}
            >
              {status === 'uploading' ? '⏳ Uploading…' : '✓ Mark as Completed'}
            </button>
            <button type="button" className={styles.uploadCancelBtn} onClick={onCancel}>
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

// ── Development Tab ───────────────────────────────────────────────────────────
function DevelopmentTab({ data, methodology, completions, onCompletionAdded }) {
  const [activeFilter, setActiveFilter] = useState('all');
  const [uploadingCourseKey, setUploadingCourseKey] = useState(null);

  const completedKeys = useMemo(() => new Set((completions || []).map(c => c.course_key)), [completions]);
  const totalBoost = useMemo(() => (completions || []).reduce((s, c) => s + (c.score_boost || 0), 0), [completions]);

  const dimIcons = useMemo(() => {
    if (!methodology) return {};
    return Object.fromEntries(methodology.dimensions.map(d => [d.id, d.icon]));
  }, [methodology]);

  const weakDims = useMemo(() => {
    if (!data?.dimensions) return [];
    return data.dimensions
      .filter(d => d.score !== null && d.score < 4.0)
      .sort((a, b) => (a.score || 5) - (b.score || 5))
      .map(d => d.id);
  }, [data]);

  const filters = [
    { id: 'all', label: 'All Resources' },
    { id: 'priority', label: '🎯 Priority Areas' },
    ...Object.keys(COURSE_CATALOG).map(id => ({
      id,
      label: `${dimIcons[id] || ''} ${methodology?.dimensions?.find(d => d.id === id)?.label || id}`,
    })),
  ];

  const visibleCourses = useMemo(() => {
    const catalog = [];
    Object.entries(COURSE_CATALOG).forEach(([dimId, courses]) => {
      courses.forEach((c, i) => catalog.push({ ...c, dimId, courseKey: `${dimId}_${i}` }));
    });
    if (activeFilter === 'all') return catalog;
    if (activeFilter === 'priority') return catalog.filter(c => weakDims.includes(c.dimId));
    return catalog.filter(c => c.dimId === activeFilter);
  }, [activeFilter, weakDims]);

  const handleUploadSuccess = useCallback((result) => {
    setUploadingCourseKey(null);
    onCompletionAdded(result);
  }, [onCompletionAdded]);

  return (
    <div className={styles.tabContent}>
      {/* Completions Summary Strip */}
      {completions && completions.length > 0 && (
        <div className={styles.completionStrip}>
          <div className={styles.completionStripIcon}>🏆</div>
          <div className={styles.completionStripText}>
            <strong>{completions.length}</strong> course{completions.length !== 1 ? 's' : ''} completed
          </div>
          <div className={styles.completionBoostBadge}>
            +{totalBoost.toFixed(2)} development bonus earned
          </div>
        </div>
      )}

      {/* AI summary */}
      <div className={styles.aiSummaryCard}>
        <div className={styles.aiSummaryHeader}>
          <div className={styles.aiSummaryIcon}>🤖</div>
          <div>
            <div className={styles.aiSummaryTitle}>AI Development Advisor</div>
            <div className={styles.aiSummarySub}>Evidence-based recommendations • Verified resources only</div>
          </div>
        </div>
        {data?.k_anonymity_met ? (
          <p className={styles.aiSummaryText}>
            {weakDims.length === 0
              ? `Outstanding performance! Your scores are strong across all dimensions. Explore the resources below to maintain excellence and stay current with best practices in higher education pedagogy.`
              : `Based on your aggregated evaluation results, the following dimensions show room for growth: ${weakDims.map(id => methodology?.dimensions?.find(d => d.id === id)?.label || id).join(', ')}. The curated courses below are sourced from verified platforms (Coursera, NPTEL, edX, MIT OCW) and matched to your specific development needs.`
            }
          </p>
        ) : (
          <p className={styles.aiSummaryText}>
            Personalized recommendations will be available once your response threshold is met.
            In the meantime, explore the full resource catalog below to proactively invest in your professional development.
          </p>
        )}
        <div className={styles.aiSummaryTags}>
          <span className={styles.aiTag}>✓ Coursera Verified</span>
          <span className={styles.aiTag}>✓ NPTEL Certified</span>
          <span className={styles.aiTag}>✓ MIT OCW Open</span>
          <span className={styles.aiTag}>✓ edX Accredited</span>
        </div>
      </div>

      {/* Filter bar */}
      <div className={styles.filterBar}>
        {filters.map(f => (
          <button
            key={f.id}
            className={`${styles.filterBtn} ${activeFilter === f.id ? styles.filterBtnActive : ''}`}
            onClick={() => setActiveFilter(f.id)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Courses Grid */}
      {visibleCourses.length === 0 ? (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>🎓</div>
          <div className={styles.emptyTitle}>No Courses in this filter</div>
          <p className={styles.emptyDesc}>Try selecting "All Resources" to see the full catalog.</p>
        </div>
      ) : (
        <div className={styles.coursesGrid}>
          {visibleCourses.map((c, i) => {
            const isPriority = weakDims.includes(c.dimId);
            const isCompleted = completedKeys.has(c.courseKey);
            const isUploadOpen = uploadingCourseKey === c.courseKey;
            return (
              <div
                key={c.courseKey}
                className={`${styles.courseCard} ${isPriority ? styles.courseCardPriority : ''} ${isCompleted ? styles.courseCardCompleted : ''}`}
                id={`course-${c.dimId}-${i}`}
              >
                {isCompleted && <div className={styles.completedBadge}>✅ Completed</div>}
                {isPriority && !isCompleted && <div className={styles.coursePriorityBadge}>🎯 Priority</div>}
                <div className={styles.courseProvider}>{c.provider}</div>
                <div className={styles.courseName}>{c.name}</div>
                <div className={styles.courseMeta}>{c.institution} · {c.duration}</div>
                <div className={styles.courseMatch}>↳ {c.match}</div>
                <div className={styles.courseDim}>
                  {dimIcons[c.dimId]} {methodology?.dimensions?.find(d => d.id === c.dimId)?.label || c.dimId}
                </div>
                <div className={styles.courseCardFooter}>
                  <a
                    href={c.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={styles.courseLink}
                    onClick={e => e.stopPropagation()}
                  >
                    Open Course →
                  </a>
                  {!isCompleted && (
                    <button
                      className={styles.uploadTriggerBtn}
                      onClick={() => setUploadingCourseKey(isUploadOpen ? null : c.courseKey)}
                    >
                      {isUploadOpen ? '✕ Cancel' : '📤 Upload Certificate'}
                    </button>
                  )}
                </div>
                {isUploadOpen && (
                  <UploadPanel
                    courseKey={c.courseKey}
                    courseName={c.name}
                    provider={c.provider}
                    dimId={c.dimId}
                    onSuccess={handleUploadSuccess}
                    onCancel={() => setUploadingCourseKey(null)}
                  />
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Disclaimer */}
      <div className={styles.disclaimerCard}>
        <strong>📌 Note:</strong> Course recommendations are matched to your evaluation dimensions.
        All linked platforms are internationally recognised and offer free or affordable access.
        NPTEL courses count toward continuing education credits recognised by AICTE.
        Completing verified courses earns a development score bonus (max +0.50).
      </div>
    </div>
  );
}

// ── Privacy Tab ───────────────────────────────────────────────────────────────
function PrivacyTab({ methodology }) {
  if (!methodology) return <div className={styles.loading}>Loading privacy information…</div>;
  return (
    <div className={styles.tabContent}>
      <div className={styles.privacyHero}>
        <div className={styles.privacyHeroIcon}>🔐</div>
        <div className={styles.privacyHeroTitle}>How Your Students' Privacy Is Protected</div>
        <p className={styles.privacyHeroDesc}>
          EduPulse is built on a foundation of trust. Every mechanism in this system
          is designed to give you meaningful feedback while ensuring that no individual
          student can ever be identified from the results you see.
        </p>
      </div>

      <div className={styles.privacyMeasures}>
        {methodology.anonymity_measures.map((m, i) => (
          <div key={i} className={styles.privacyMeasure}>
            <div className={styles.privacyMeasureNum}>{i + 1}</div>
            <div className={styles.privacyMeasureText}>{m}</div>
          </div>
        ))}
      </div>

      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.cardTitle}>🔑 K-Anonymity Threshold</div>
        </div>
        <p style={{ fontSize: 14, color: '#2C3D3C', lineHeight: 1.7 }}>
          {methodology.k_anonymity.description}
        </p>
        <div className={styles.kBadge}>
          Minimum threshold: <strong>k = {methodology.k_anonymity.threshold} responses</strong>
        </div>
      </div>

      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.cardTitle}>📊 What You Can and Cannot See</div>
        </div>
        <div className={styles.canTable}>
          <div className={styles.canCol}>
            <div className={styles.canColHeader} style={{ color: '#1E6F4A' }}>✅ You CAN see</div>
            {[
              'Your aggregated dimension scores (if ≥5 responses)',
              'Your composite score and performance band',
              'Your term-over-term trend data',
              'AI-generated interpretive summaries',
              'Recommended development resources',
            ].map((item, i) => (
              <div key={i} className={styles.canItem}><span style={{ color: '#1E6F4A' }}>✓</span> {item}</div>
            ))}
          </div>
          <div className={styles.canCol}>
            <div className={styles.canColHeader} style={{ color: '#9A3C2C' }}>❌ You CANNOT see</div>
            {[
              'Individual student responses or ratings',
              'Which student gave which score',
              'Verbatim student comments',
              'Student identifiers (name, roll number, etc.)',
              'Scores below the k-anonymity threshold',
            ].map((item, i) => (
              <div key={i} className={styles.canItem}><span style={{ color: '#9A3C2C' }}>✗</span> {item}</div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function EvaluationTransparency({ facultyProfileId }) {
  const [activeTab, setActiveTab] = useState('questionnaire');
  const [methodology, setMethodology] = useState(null);
  const [strengthsData, setStrengthsData] = useState(null);
  const [completions, setCompletions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    Promise.all([
      DB.getMethodology(),
      DB.getMyStrengthsWeaknesses(),
      DB.getCompletedCourses(),
    ]).then(([meth, sw, comp]) => {
      if (!cancelled) {
        setMethodology(meth);
        setStrengthsData(sw);
        setCompletions(comp?.completions || []);
        setLoading(false);
      }
    }).catch(() => {
      if (!cancelled) setLoading(false);
    });
    return () => { cancelled = true; };
  }, []);

  const totalBoost = useMemo(() => completions.reduce((s, c) => s + (c.score_boost || 0), 0), [completions]);
  const adjustedScore = useMemo(() => {
    if (!strengthsData?.composite_score) return null;
    return Math.min(5.0, strengthsData.composite_score + totalBoost);
  }, [strengthsData, totalBoost]);

  const handleCompletionAdded = useCallback((result) => {
    setCompletions(prev => [...prev, {
      id: result.id,
      course_key: result.course_key,
      course_name: result.course_name,
      provider: result.provider,
      dimension_id: result.dimension_id,
      score_boost: result.score_boost,
      completed_at: result.completed_at,
    }]);
  }, []);

  const tabs = [
    { id: 'questionnaire', label: 'Questionnaire',  icon: '📋' },
    { id: 'results',       label: 'My Results',     icon: '📊' },
    { id: 'history',       label: 'History',        icon: '📈' },
    { id: 'development',   label: 'Development',    icon: '🎓' },
    { id: 'privacy',       label: 'Privacy Policy', icon: '🔐' },
  ];

  return (
    <div className={styles.root}>
      <div className={styles.header}>
        <div className={styles.headerIcon}>🔍</div>
        <div>
          <div className={styles.headerTitle}>Evaluation Transparency Centre</div>
          <div className={styles.headerSub}>
            Understand how you're evaluated, what your students said (anonymously), and how to grow
          </div>
        </div>
      </div>

      <div className={styles.tabBar} role="tablist">
        {tabs.map(t => (
          <Tab key={t.id} {...t} active={activeTab === t.id} onClick={setActiveTab} />
        ))}
      </div>

      <div className={styles.body} role="tabpanel">
        {loading ? (
          <div className={styles.loadingFull}>
            <div className={styles.loadingSpinner} />
            <div>Loading transparency data…</div>
          </div>
        ) : (
          <>
            {activeTab === 'questionnaire' && <QuestionnaireTab methodology={methodology} />}
            {activeTab === 'results'       && <MyResultsTab data={strengthsData} completions={completions} totalBoost={totalBoost} adjustedScore={adjustedScore} />}
            {activeTab === 'history'       && <HistoryTab data={strengthsData} />}
            {activeTab === 'development'   && <DevelopmentTab data={strengthsData} methodology={methodology} completions={completions} onCompletionAdded={handleCompletionAdded} />}
            {activeTab === 'privacy'       && <PrivacyTab methodology={methodology} />}
          </>
        )}
      </div>
    </div>
  );
}
