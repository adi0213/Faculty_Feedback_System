import React, { useMemo, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { DB } from '../../data/db';
import { compositeScore, scoreToBand } from '../../data/advisor';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend
} from 'recharts';
import styles from '../Faculty/FacultyDashboard.module.css';
import hodStyles from './HoDDashboard.module.css';

const DIMS = ['clarity','punctuality','fairness','approachability','methodology','pacing'];
const DEPT_AVG = 3.6;
const UNIV_AVG = 3.5;

function FacultyModal({ fac, onClose }) {
  if (!fac) return null;
  const avg  = compositeScore(fac.scores);
  const band = scoreToBand(avg);
  return (
    <div className={hodStyles.modalOverlay} onClick={e => e.target === e.currentTarget && onClose()}>
      <div className={hodStyles.modal}>
        <button className={hodStyles.modalClose} onClick={onClose}>✕</button>
        <div className={hodStyles.modalHeader}>
          <div className={hodStyles.modalAvatar}>{fac.name.split(' ').map(w=>w[0]).join('').slice(0,2).toUpperCase()}</div>
          <div>
            <div className={hodStyles.modalName}>{fac.name}</div>
            <div className={hodStyles.modalMeta}>{fac.code} · {fac.subject} · {fac.responses} responses</div>
          </div>
        </div>
        <div className={`${styles.bandChip} ${styles[`band_${band.cls}`]}`} style={{marginBottom:16}}>
          {band.icon} {band.band} — {avg}/5
        </div>
        {DIMS.map(d => {
          const score = fac.scores[d] || 0;
          const color = score >= 4 ? '#1E6F4A' : score >= 3 ? '#C9954A' : '#9A3C2C';
          return (
            <div key={d} className={hodStyles.miniBar}>
              <span className={hodStyles.miniLabel}>{d}</span>
              <div className={hodStyles.miniTrack}>
                <div className={hodStyles.miniFill} style={{width:`${(score/5)*100}%`, background: color}} />
              </div>
              <span className={hodStyles.miniScore} style={{color}}>{score.toFixed(1)}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function HoDDashboard() {
  const { user } = useAuth();
  const [faculties, setFaculties] = React.useState([]);
  
  React.useEffect(() => {
    DB.getFacultiesByDept(user.dept, user.college).then(setFaculties);
  }, [user]);
  const [modalFac, setModalFac] = useState(null);

  const bandCounts = { strong: 0, developing: 0, needs: 0 };
  faculties.forEach(f => bandCounts[f.band] = (bandCounts[f.band] || 0) + 1);

  const deptDimData = DIMS.map(d => ({
    name: d.slice(0,4).toUpperCase(),
    Dept: +(faculties.reduce((s,f) => s + (f.scores[d]||0), 0) / (faculties.length || 1)).toFixed(2),
    Univ: UNIV_AVG + (Math.random() * .3 - .15),
  }));

  const pieData = [
    { name: 'Strong',     value: bandCounts.strong,     color: '#1E6F4A' },
    { name: 'Developing', value: bandCounts.developing, color: '#C9954A' },
    { name: 'Needs Supp', value: bandCounts.needs,      color: '#9A3C2C' },
  ];

  const flags = [
    { type: 'bias',   code: 'FAC-0114 · OS-305', msg: 'Temporal-clustering flag: 4 extreme-low ratings in <6 min after grade release. Routed for manual review — not auto-excluded.' },
    { type: 'low-n',  code: 'FAC-0309 · CN-410', msg: `Only ${faculties.find(f=>f.code==='FAC-0309')?.responses||3} responses — below k-anonymity threshold (min 5). Report withheld pending more participation.` },
  ];

  return (
    <div>
      <div className={styles.pageHeader}>
        <div className={styles.breadcrumb}>🏛️ HoD Portal</div>
        <h1 className={styles.pageTitle}>Dept. of {user.dept}</h1>
        <p className={styles.pageSub}>{user.college} · {user.university}</p>
      </div>

      <div className={styles.bento} style={{gridTemplateColumns:'repeat(12,1fr)'}}>

        {/* KPIs */}
        {[
          { label:'Participation', value:'78%', note:'↑ Good rate' },
          { label:'Faculty Count', value: faculties.length, note:'In your dept.' },
          { label:'Review Flags',  value: flags.length,     note:'Awaiting action', red: true },
          { label:'Below k-min',  value: faculties.filter(f=>f.responses<5).length, note:'Need more responses' },
        ].map((k,i) => (
          <div key={i} className={`${styles.card} ${styles.span3}`}>
            <div className={styles.kpiLabel}>{k.label}</div>
            <div className={styles.kpiValue} style={k.red?{color:'#9A3C2C'}:{}}>{k.value}</div>
            <div className={styles.kpiNote}>{k.note}</div>
          </div>
        ))}

        {/* Faculty Roster */}
        <div className={`${styles.card} ${styles.span7}`}>
          <div className={styles.cardHeader}>
            <div className={styles.cardTitle}>👥 Faculty Roster — {user.dept}</div>
          </div>
          <div className={styles.tableWrap}>
            <table>
              <thead>
                <tr><th>Faculty</th><th>Subject</th><th>Responses</th><th>Score</th><th>Band</th><th></th></tr>
              </thead>
              <tbody>
                {faculties.map(fac => {
                  const avg  = compositeScore(fac.scores);
                  const band = scoreToBand(avg);
                  const lowN = fac.responses < 5;
                  return (
                    <tr key={fac.id}>
                      <td style={{fontWeight:600}}>{fac.name}</td>
                      <td style={{fontSize:12,color:'#4A5E5A'}}>{fac.subject.split(' ').slice(0,3).join(' ')}</td>
                      <td><span className={styles.mono}>{fac.responses}</span>{lowN && <span className={hodStyles.flagLow}> LOW n</span>}</td>
                      <td><span className={styles.mono}>{avg}</span></td>
                      <td><span className={`${styles.bandChip} ${styles[`band_${band.cls}`]}`} style={{padding:'3px 10px',fontSize:11}}>{band.band}</span></td>
                      <td><button className={hodStyles.detailBtn} onClick={()=>setModalFac(fac)}>Details</button></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Dept vs Univ bar */}
        <div className={`${styles.card} ${styles.span5}`}>
          <div className={styles.cardHeader}>
            <div className={styles.cardTitle}>📊 Dept vs University</div>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={deptDimData} barCategoryGap="30%">
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(13,31,30,.06)" />
              <XAxis dataKey="name" tick={{fontSize:10,fill:'#8A9E99'}} axisLine={false} tickLine={false} />
              <YAxis domain={[0,5]} tick={{fontSize:10,fill:'#8A9E99'}} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{background:'#FDFAF4',border:'1px solid rgba(13,31,30,.1)',borderRadius:10,fontSize:12}} />
              <Bar dataKey="Dept" fill="#2E6B60" radius={[4,4,0,0]} />
              <Bar dataKey="Univ" fill="#C7D6D1" radius={[4,4,0,0]} />
              <Legend iconSize={10} wrapperStyle={{fontSize:11}} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Flags */}
        <div className={`${styles.card} ${styles.span8}`}>
          <div className={styles.cardHeader}>
            <div className={styles.cardTitle}>⚠️ Flags Requiring Attention</div>
            <span style={{fontSize:11,padding:'3px 10px',background:'#F4DDD8',color:'#9A3C2C',border:'1px solid rgba(154,60,44,.2)',borderRadius:9999}}>
              {flags.length} flag{flags.length !== 1 ? 's' : ''}
            </span>
          </div>
          {flags.map((f,i) => (
            <div key={i} className={`${hodStyles.flagStrip} ${f.type==='low-n'?hodStyles.flagStripLow:''}`}>
              <strong className={styles.mono}>{f.code}</strong><br/><span style={{fontSize:12.5,color:'#4A5E5A'}}>{f.msg}</span>
            </div>
          ))}
        </div>

        {/* Band Pie */}
        <div className={`${styles.card} ${styles.span4}`}>
          <div className={styles.cardHeader}>
            <div className={styles.cardTitle}>🎯 Band Distribution</div>
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={48} outerRadius={72} dataKey="value" strokeWidth={2} stroke="#F2EDE2">
                {pieData.map((e,i) => <Cell key={i} fill={e.color} />)}
              </Pie>
              <Legend iconSize={10} wrapperStyle={{fontSize:11}} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Policy note */}
        <div className={`${styles.card} ${styles.span12}`} style={{background:'linear-gradient(145deg,#EBF5F3,#FDFAF4)',borderColor:'rgba(74,144,136,.18)'}}>
          <div style={{display:'flex',alignItems:'flex-start',gap:16}}>
            <span style={{fontSize:32}}>⚖️</span>
            <div>
              <div style={{fontFamily:"'Playfair Display',serif",fontSize:'1rem',fontWeight:600,color:'#0D2B2B',marginBottom:6}}>Non-Punitive Governance Policy</div>
              <div style={{fontSize:13,color:'#4A5E5A',lineHeight:1.65}}>Scores displayed here are formative <em>bands</em>, not rankings. Individual student responses are never visible at this level. Any escalation beyond this dashboard requires an authorized, audited request under the system's due-process protocol.</div>
            </div>
          </div>
        </div>
      </div>

      {/* Faculty Detail Modal */}
      <FacultyModal fac={modalFac} onClose={() => setModalFac(null)} />
    </div>
  );
}
