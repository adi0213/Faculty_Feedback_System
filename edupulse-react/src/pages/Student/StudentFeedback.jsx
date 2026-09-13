import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../../context/AuthContext';
import { DB } from '../../data/db';
import { buildSession, answerQuestion, computeScores, computeScoresDisplay } from '../../data/engine';
import styles from './StudentFeedback.module.css';

const TOTAL = 10;

/* ── Faculty Select Screen ── */
function FacultySelect({ faculties, onSelect }) {
  return (
    <div>
      <div className={styles.pageHeader}>
        <div className={styles.breadcrumb}>📋 Feedback Portal</div>
        <h1 className={styles.pageTitle}>Submit Faculty Feedback</h1>
        <p className={styles.pageSub}>
          Select a faculty from your enrolled courses. Each faculty can receive feedback once per term.
        </p>
      </div>

      <div className={styles.facultyList}>
        {faculties.map((fac, i) => {
          const done = fac.done;
          const initials = fac.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
          return (
            <div
              key={fac.id}
              className={`${styles.facultyCard} ${done ? styles.facultyDone : ''}`}
              style={{ animationDelay: `${i * 55}ms` }}
            >
              <div className={styles.facultyAvatar}>{initials}</div>
              <div className={styles.facultyInfo}>
                <div className={styles.facultyName}>{fac.name}</div>
                <div className={styles.facultySubject}>{fac.subject}</div>
                <div className={styles.facultyMeta}>{fac.code} · {fac.dept} · {fac.college}</div>
              </div>
              <div className={styles.facultyAction}>
                {done
                  ? <span className={styles.doneBadge}>✓ Submitted</span>
                  : <button className={styles.startBtn} onClick={() => onSelect(fac)}>
                      Start Feedback →
                    </button>
                }
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ── Sub-question Multi-Select Component ── */
function SubQuestionPanel({ question, onConfirm, animating }) {
  const [selected, setSelected] = useState(new Set());
  const [otherText, setOtherText] = useState('');
  const [showOther, setShowOther] = useState(false);

  const toggleOption = (val) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(val)) {
        next.delete(val);
      } else {
        next.add(val);
      }
      return next;
    });
  };

  const canConfirm = selected.size > 0 || (showOther && otherText.trim().length > 0);

  const handleConfirm = () => {
    if (!canConfirm || animating) return;
    const selectedValues = [...selected];
    const selectedLabels = question.options
      .filter(o => selected.has(o.value))
      .map(o => o.label);
    const finalOther = showOther && otherText.trim() ? otherText.trim() : null;
    if (showOther && finalOther && selectedValues.length === 0) {
      selectedValues.push(0); // sentinel for "other only"
      selectedLabels.push('Other');
    }
    onConfirm(selectedValues, selectedLabels.join(', '), finalOther);
  };

  return (
    <div className={styles.subMultiPanel}>
      <p className={styles.subMultiHint}>Select all that apply:</p>
      <div className={styles.subCheckGrid}>
        {question.options.map((opt) => {
          const checked = selected.has(opt.value);
          return (
            <button
              key={opt.value}
              className={`${styles.subCheckCard} ${checked ? styles.subCheckSelected : ''}`}
              onClick={() => toggleOption(opt.value)}
              disabled={animating}
              type="button"
            >
              <span className={styles.subCheckBox}>
                {checked ? '☑' : '☐'}
              </span>
              <span className={styles.subCheckIcon}>{opt.icon}</span>
              <div className={styles.subCheckContent}>
                <div className={styles.subCheckLabel}>{opt.label}</div>
                <div className={styles.subCheckDesc}>{opt.desc}</div>
              </div>
            </button>
          );
        })}

        {/* Other option toggle */}
        <button
          className={`${styles.subCheckCard} ${styles.subCheckOtherCard} ${showOther ? styles.subCheckSelected : ''}`}
          onClick={() => setShowOther(v => !v)}
          disabled={animating}
          type="button"
        >
          <span className={styles.subCheckBox}>{showOther ? '☑' : '☐'}</span>
          <span className={styles.subCheckIcon}>✏️</span>
          <div className={styles.subCheckContent}>
            <div className={styles.subCheckLabel}>Other / Specify</div>
            <div className={styles.subCheckDesc}>My situation isn't listed above</div>
          </div>
        </button>
      </div>

      {/* Other text field */}
      {showOther && (
        <div className={styles.otherFieldWrap}>
          <label className={styles.otherLabel}>Please describe your concern:</label>
          <textarea
            className={styles.otherInput}
            value={otherText}
            onChange={e => setOtherText(e.target.value)}
            placeholder="Describe what you observed in your own words..."
            rows={3}
            maxLength={300}
            autoFocus
          />
          <div className={styles.otherCount}>{otherText.length}/300</div>
        </div>
      )}

      <button
        className={`${styles.subConfirmBtn} ${!canConfirm ? styles.subConfirmDisabled : ''}`}
        onClick={handleConfirm}
        disabled={!canConfirm || animating}
        type="button"
      >
        Confirm Selection →
      </button>
    </div>
  );
}

/* ── Feedback Form Screen ── */
function FeedbackForm({ faculty, onComplete, onBack }) {
  const [session, setSession] = useState(null);
  const [currentQ, setCurrentQ] = useState(null);
  const [selected, setSelected] = useState(null);
  const [animating, setAnimating] = useState(false);
  const [progress, setProgress] = useState({ shown: 0, total: TOTAL });

  useEffect(() => {
    const s = buildSession();
    setSession(s);
    setCurrentQ(s.queue[0]);
    setProgress({ shown: 0, total: TOTAL });
  }, [faculty.id]);

  // Handle single-select (main questions)
  const handleSelect = useCallback(async (opt) => {
    if (animating || !session || !currentQ) return;

    setSelected(opt.value);
    setAnimating(true);
    await new Promise(r => setTimeout(r, 320));

    const newSession = answerQuestion(session, currentQ.id, opt.value, opt.label);
    const newShown = newSession.shown.length;
    setProgress({ shown: newShown, total: TOTAL });

    if (newSession.done || newSession.queue.length === 0) {
      const scores = computeScores(newSession.answers);
      setAnimating(false);
      setSelected(null);
      onComplete(scores, newSession.answers);
    } else {
      setSession(newSession);
      setCurrentQ(newSession.queue[0]);
      setSelected(null);
      setAnimating(false);
    }
  }, [animating, session, currentQ, onComplete]);

  // Handle multi-select (sub-questions)
  const handleSubConfirm = useCallback(async (values, labels, otherText) => {
    if (animating || !session || !currentQ) return;

    setAnimating(true);
    await new Promise(r => setTimeout(r, 300));

    const newSession = answerQuestion(session, currentQ.id, values, labels, otherText);
    const newShown = newSession.shown.length;
    setProgress({ shown: newShown, total: TOTAL });

    if (newSession.done || newSession.queue.length === 0) {
      const scores = computeScores(newSession.answers);
      setAnimating(false);
      onComplete(scores, newSession.answers);
    } else {
      setSession(newSession);
      setCurrentQ(newSession.queue[0]);
      setAnimating(false);
    }
  }, [animating, session, currentQ, onComplete]);

  if (!currentQ) return <div className={styles.loadingQ}>Loading questions…</div>;

  const pct = Math.round((progress.shown / progress.total) * 100);
  const initials = faculty.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();

  return (
    <div>
      {/* Progress header */}
      <div className={styles.progressCard}>
        <div className={styles.progressTop}>
          <div className={styles.progressFacInfo}>
            <div className={styles.progressAvatar}>{initials}</div>
            <div>
              <div className={styles.progressFacName}>{faculty.name}</div>
              <div className={styles.progressFacSubj}>{faculty.subject} · {faculty.dept}</div>
            </div>
          </div>
          <div className={styles.progressCount}>
            {progress.shown + 1} <span>/</span> {TOTAL}
          </div>
        </div>
        <div className={styles.progressBarWrap}>
          <div
            className={styles.progressBarFill}
            style={{ width: `${Math.max(pct, 8)}%` }}
          />
        </div>
      </div>

      {/* Question card */}
      <div
        className={`${styles.questionCard} ${animating ? styles.questionOut : styles.questionIn}`}
        key={currentQ.id}
      >
        {/* Badge */}
        <div className={`${styles.qBadge} ${currentQ.isSub ? styles.qBadgeSub : styles.qBadgeMain}`}>
          {currentQ.isSub
            ? `⚡ Follow-up — Question ${progress.shown + 1} of ${TOTAL}`
            : `📋 Question ${progress.shown + 1} of ${TOTAL}`
          }
        </div>

        {/* Sub-question note */}
        {currentQ.isSub && (
          <div className={styles.subNote}>
            💡 Based on your previous response, tell us more:
          </div>
        )}

        {/* Question text */}
        <p className={styles.questionText}>{currentQ.text}</p>

        {/* Multi-select for sub-questions, single-select for main */}
        {currentQ.isSub ? (
          <SubQuestionPanel
            question={currentQ}
            onConfirm={handleSubConfirm}
            animating={animating}
          />
        ) : (
          <div className={styles.optionsGrid}>
            {currentQ.options.map((opt, idx) => (
              <button
                key={opt.value}
                className={`${styles.optCard} ${styles[`mood_${opt.mood}`]} ${selected === opt.value ? styles.optSelected : ''}`}
                onClick={() => handleSelect(opt)}
                disabled={animating}
                style={{ animationDelay: `${idx * 45}ms` }}
              >
                <span className={styles.optIcon}>{opt.icon}</span>
                <div className={styles.optText}>
                  <div className={styles.optLabel}>{opt.label}</div>
                  <div className={styles.optDesc}>{opt.desc}</div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      <div className={styles.backLink}>
        <button onClick={onBack}>← Back to Faculty List</button>
      </div>
    </div>
  );
}

/* ── Comment + Submit Screen ── */
function SubmitScreen({ faculty, scores, answers, onSubmit, onBack }) {
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    if (submitting) return;
    setSubmitting(true);
    setError('');
    try {
      await onSubmit(scores, comment);
    } catch (e) {
      setError(e.message || 'Failed to submit feedback. Please try again.');
      setSubmitting(false);
    }
  };

  const negativeAnswers = Object.values(answers).filter(a => {
    const v = Array.isArray(a.value) ? Math.min(...a.value) : a.value;
    return v <= 2 && !a.isSub;
  });

  return (
    <div className={styles.submitScreen}>
      <div className={styles.submitCard}>
        <div className={styles.submitHeader}>
          <div className={styles.checkIcon}>✓</div>
          <h2 className={styles.submitTitle}>Questions Completed!</h2>
          <p className={styles.submitSub}>
            You answered all {TOTAL} questions for <strong>{faculty.name}</strong>.
            Add any optional comments below, then submit.
          </p>
        </div>

        {negativeAnswers.length > 0 && (
          <div className={styles.summaryNote}>
            <span>💡</span>
            <span>{negativeAnswers.length} dimension{negativeAnswers.length > 1 ? 's' : ''} flagged for improvement — your feedback will help generate a personalized development plan for this faculty.</span>
          </div>
        )}

        <div className={styles.commentField}>
          <label className={styles.commentLabel}>📝 Additional Comments (Optional & Anonymous)</label>
          <textarea
            className={styles.commentBox}
            placeholder="Share any specific observations, suggestions, or feedback... Your response is completely anonymous."
            value={comment}
            onChange={e => setComment(e.target.value)}
            rows={4}
          />
        </div>

        {error && (
          <div className={styles.submitError}>
            ⚠️ {error}
          </div>
        )}

        <button
          className={`${styles.submitFinalBtn} ${submitting ? styles.submitting : ''}`}
          onClick={handleSubmit}
          disabled={submitting}
        >
          {submitting ? '⏳ Submitting anonymously…' : '🔒 Submit Feedback Anonymously'}
        </button>

        <div className={styles.privacyNote}>
          Your identity has been separated from this submission using a pseudonymous token. No one can link this feedback to you.
        </div>

        <div className={styles.backLink} style={{marginTop:'12px'}}>
          <button onClick={onBack}>← Review answers</button>
        </div>
      </div>
    </div>
  );
}

/* ── Success Screen ── */
function SuccessScreen({ faculty, onAnother }) {
  return (
    <div className={styles.successScreen}>
      <div className={styles.successIcon}>✓</div>
      <h2 className={styles.successTitle}>Feedback Submitted!</h2>
      <p className={styles.successSub}>
        Thank you for contributing to teaching excellence. Your anonymous feedback for <strong>{faculty.name}</strong> has been recorded.
      </p>
      <div className={styles.privacyBadge}>
        🔒 Identity separated · Pseudonymous token issued · DPDP Act 2023 Compliant
      </div>
      <button className={styles.anotherBtn} onClick={onAnother}>
        ← Submit More Feedback
      </button>
    </div>
  );
}

/* ── Main Page ── */
export default function StudentFeedback() {
  const { user } = useAuth();
  const [screen, setScreen]           = useState('select');
  const [faculties, setFaculties]     = useState([]);
  const [selectedFac, setSelectedFac] = useState(null);
  const [scores, setScores]           = useState(null);
  const [answers, setAnswers]         = useState(null);

  const loadFaculties = useCallback(async () => {
    const facs = await DB.getEnrolledFaculties();
    const enriched = await Promise.all(facs.map(async f => {
      const done = await DB.hasSubmitted(f.id);
      return { ...f, done };
    }));
    setFaculties(enriched);
  }, []);

  useEffect(() => {
    loadFaculties();
  }, [user.id]);

  const handleSelectFaculty = (fac) => {
    setSelectedFac(fac);
    setScreen('form');
  };

  const handleFormComplete = (sc, ans) => {
    setScores(sc);
    setAnswers(ans);
    setScreen('submit');
  };

  const handleFinalSubmit = async (sc, comment) => {
    // sc is already 1-4 int scores from computeScores()
    await DB.submitFeedback(selectedFac.id, sc, comment);
    setScreen('success');
  };

  const backToSelect = () => {
    setSelectedFac(null);
    setScores(null);
    setAnswers(null);
    setScreen('select');
    loadFaculties();
  };

  return (
    <div className={styles.page}>
      {screen === 'select' && (
        <FacultySelect
          faculties={faculties}
          onSelect={handleSelectFaculty}
          studentId={user.id}
        />
      )}
      {screen === 'form' && selectedFac && (
        <FeedbackForm
          faculty={selectedFac}
          onComplete={handleFormComplete}
          onBack={backToSelect}
        />
      )}
      {screen === 'submit' && selectedFac && (
        <SubmitScreen
          faculty={selectedFac}
          scores={scores}
          answers={answers}
          onSubmit={handleFinalSubmit}
          onBack={() => setScreen('form')}
        />
      )}
      {screen === 'success' && selectedFac && (
        <SuccessScreen faculty={selectedFac} onAnother={backToSelect} />
      )}
    </div>
  );
}
