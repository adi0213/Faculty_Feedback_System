import React, { useMemo } from 'react';
import { useAuth } from '../../context/AuthContext';
import { DB } from '../../data/db';
import { compositeScore } from '../../data/advisor';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Legend, ScatterChart, Scatter, ZAxis
} from 'recharts';
import styles from '../Faculty/FacultyDashboard.module.css';

export default function UniversityDashboard() {
  const { user } = useAuth();
  
  const [faculties, setFaculties] = React.useState([]);
  
  React.useEffect(() => {
    DB.getAllFaculties().then(setFaculties);
  }, []);
  
  const totalResponses = faculties.reduce((s, f) => s + f.responses, 0);
  const overallAvg = faculties.length ? +(faculties.reduce((s, f) => s + compositeScore(f.scores), 0) / faculties.length).toFixed(2) : 0;

  // College participation
  const colPartData = [
    { name: 'GEC Thrissur', responses: totalResponses, avg: overallAvg },
    { name: 'CET Trivandrum', responses: 840, avg: 3.8 },
    { name: 'TKM Kollam', responses: 620, avg: 3.6 },
    { name: 'NSS Palakkad', responses: 410, avg: 3.4 },
  ];

  // System adoption trend
  const adoptionData = [
    { month: 'Jan', colleges: 2, students: 400 },
    { month: 'Feb', colleges: 5, students: 1200 },
    { month: 'Mar', colleges: 12, students: 3500 },
    { month: 'Apr', colleges: 24, students: 8900 },
    { month: 'May', colleges: 45, students: 15400 },
  ];

  // FDP Impact (Before/After)
  const fdpImpactData = [
    { dim: 'Clarity', before: 3.2, after: 3.8 },
    { dim: 'Methodology', before: 2.9, after: 3.6 },
    { dim: 'Engagement', before: 3.1, after: 3.9 },
    { dim: 'Assessment', before: 3.4, after: 3.7 },
  ];

  return (
    <div>
      <div className={styles.pageHeader}>
        <div className={styles.breadcrumb}>🌐 University Portal</div>
        <h1 className={styles.pageTitle}>{user.university}</h1>
        <p className={styles.pageSub}>Statewide Aggregate Dashboard</p>
      </div>

      <div className={styles.bento} style={{gridTemplateColumns:'repeat(12,1fr)'}}>
        
        {/* Top KPIs */}
        {[
          { label: 'Participating Colleges', value: 45, note: '+21 this semester' },
          { label: 'Total Feedback Collected', value: '15.4k', note: 'Secure & Anonymous' },
          { label: 'System-Wide Average', value: overallAvg, note: 'Target: 3.5' },
          { label: 'AI Plans Generated', value: '842', note: 'Personalized pathways' },
        ].map((k,i) => (
          <div key={i} className={`${styles.card} ${styles.span3} ${styles.kpiCard}`}>
            <div className={styles.kpiLabel}>{k.label}</div>
            <div className={styles.kpiValue} style={{color: k.value === overallAvg ? '#2E6B60' : '#0D2B2B'}}>{k.value}</div>
            <div className={styles.kpiNote}>{k.note}</div>
          </div>
        ))}

        {/* System Adoption Trend */}
        <div className={`${styles.card} ${styles.span8}`}>
          <div className={styles.cardHeader}>
            <div className={styles.cardTitle}>📈 System Adoption (Statewide)</div>
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={adoptionData}>
              <defs>
                <linearGradient id="colorStudents" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2E6B60" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#2E6B60" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(13,31,30,.06)" />
              <XAxis dataKey="month" tick={{fontSize:10,fill:'#8A9E99'}} axisLine={false} tickLine={false} />
              <YAxis tick={{fontSize:10,fill:'#8A9E99'}} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{background:'#FDFAF4',border:'1px solid rgba(13,31,30,.1)',borderRadius:10,fontSize:12}} />
              <Area type="monotone" dataKey="students" name="Total Responses" stroke="#2E6B60" strokeWidth={3} fillOpacity={1} fill="url(#colorStudents)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* College Participation */}
        <div className={`${styles.card} ${styles.span4}`}>
          <div className={styles.cardHeader}>
            <div className={styles.cardTitle}>🏫 Top Colleges (Responses)</div>
          </div>
          <div className={styles.tableWrap}>
            <table>
              <tbody>
                {colPartData.map((c, i) => (
                  <tr key={i}>
                    <td style={{fontWeight:600, fontSize:12}}>{c.name}</td>
                    <td style={{textAlign:'right'}}><span className={styles.mono}>{c.responses}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* FDP Impact Analysis */}
        <div className={`${styles.card} ${styles.span7}`}>
          <div className={styles.cardHeader}>
            <div className={styles.cardTitle}>🎓 FDP Impact Analysis (Post AI-Recommendation)</div>
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={fdpImpactData} margin={{top: 20}}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(13,31,30,.06)" />
              <XAxis dataKey="dim" tick={{fontSize:11,fill:'#4A5E5A'}} axisLine={false} tickLine={false} />
              <YAxis domain={[0, 5]} tick={{fontSize:10,fill:'#8A9E99'}} axisLine={false} tickLine={false} />
              <Tooltip cursor={{fill:'rgba(201,149,74,.05)'}} contentStyle={{background:'#FDFAF4',border:'1px solid rgba(13,31,30,.1)',borderRadius:10,fontSize:12}} />
              <Legend iconSize={10} wrapperStyle={{fontSize:11}} />
              <Bar dataKey="before" name="Score Before FDP" fill="#D4ECE9" radius={[4,4,0,0]} />
              <Bar dataKey="after" name="Score After FDP" fill="#4A9088" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* System Health / Compliance */}
        <div className={`${styles.card} ${styles.span5}`}>
          <div className={styles.cardHeader}>
            <div className={styles.cardTitle}>🛡️ System Governance & Health</div>
          </div>
          <div style={{display:'flex', flexDirection:'column', gap: 12}}>
            <div style={{padding:16, background:'#E0F5EB', borderRadius:12, border:'1px solid rgba(30,111,74,.2)'}}>
              <div style={{fontSize:12, fontWeight:700, color:'#1E6F4A', marginBottom:4}}>✓ DPDP Act 2023 Compliant</div>
              <div style={{fontSize:11, color:'#2C3D3C'}}>All 15.4k responses pseudonymized. Zero data breaches.</div>
            </div>
            <div style={{padding:16, background:'#EBF5F3', borderRadius:12, border:'1px solid rgba(74,144,136,.2)'}}>
              <div style={{fontSize:12, fontWeight:700, color:'#2E6B60', marginBottom:4}}>✓ NAAC SSS Integration Ready</div>
              <div style={{fontSize:11, color:'#2C3D3C'}}>Export formats aligned with NAAC Student Satisfaction Survey criteria.</div>
            </div>
            <div style={{padding:16, background:'#F3E9D3', borderRadius:12, border:'1px solid rgba(201,149,74,.3)'}}>
              <div style={{fontSize:12, fontWeight:700, color:'#9C7423', marginBottom:4}}>⚠️ Adoption Gap Identified</div>
              <div style={{fontSize:11, color:'#7A5A20'}}>12 colleges have &lt; 20% participation rate. Targeted outreach planned.</div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
