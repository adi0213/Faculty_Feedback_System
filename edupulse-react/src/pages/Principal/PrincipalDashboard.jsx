import React, { useMemo } from 'react';
import { useAuth } from '../../context/AuthContext';
import { DB } from '../../data/db';
import { compositeScore } from '../../data/advisor';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, LineChart, Line
} from 'recharts';
import styles from '../Faculty/FacultyDashboard.module.css';

export default function PrincipalDashboard() {
  const { user } = useAuth();
  
  const [faculties, setFaculties] = React.useState([]);
  
  React.useEffect(() => {
    DB.getFacultiesByCollege(user.college).then(setFaculties);
  }, [user]);
  
  // Aggregate by department
  const depts = {};
  faculties.forEach(f => {
    if (!depts[f.dept]) depts[f.dept] = { name: f.dept, count: 0, totalScore: 0, strong: 0, developing: 0, needs: 0 };
    const avg = compositeScore(f.scores);
    depts[f.dept].count++;
    depts[f.dept].totalScore += avg;
    
    if (avg >= 4.0) depts[f.dept].strong++;
    else if (avg >= 3.0) depts[f.dept].developing++;
    else depts[f.dept].needs++;
  });
  
  const deptData = Object.values(depts).map(d => ({
    ...d,
    avgScore: +(d.totalScore / d.count).toFixed(2),
  }));
  
  const trendData = ['S1 2024','S2 2024','S1 2025','S2 2025'].map((t, i) => ({
    term: t,
    score: +(3.3 + (i * 0.1) + (Math.random() * 0.1)).toFixed(2) // mock trend
  }));

  const overallAvg = deptData.length ? +(deptData.reduce((s,d) => s + d.avgScore, 0) / deptData.length).toFixed(2) : 0;

  return (
    <div>
      <div className={styles.pageHeader}>
        <div className={styles.breadcrumb}>🎩 Principal Portal</div>
        <h1 className={styles.pageTitle}>{user.college}</h1>
        <p className={styles.pageSub}>{user.university}</p>
      </div>

      <div className={styles.bento} style={{gridTemplateColumns:'repeat(12,1fr)'}}>
        
        {/* Top KPIs */}
        {[
          { label: 'College Average', value: overallAvg, note: 'Out of 5.0' },
          { label: 'Total Faculties', value: faculties.length, note: 'Across all depts' },
          { label: 'Strong Performers', value: `${Math.round((deptData.reduce((s,d)=>s+d.strong,0)/(faculties.length||1))*100)}%`, note: 'Band: Strong' },
        ].map((k,i) => (
          <div key={i} className={`${styles.card} ${styles.span4} ${styles.kpiCard}`}>
            <div className={styles.kpiLabel}>{k.label}</div>
            <div className={styles.kpiValue}>{k.value}</div>
            <div className={styles.kpiNote}>{k.note}</div>
          </div>
        ))}

        {/* Dept Comparison Bar */}
        <div className={`${styles.card} ${styles.span8}`}>
          <div className={styles.cardHeader}>
            <div className={styles.cardTitle}>📊 Department Comparison</div>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={deptData} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="rgba(13,31,30,.06)" />
              <XAxis type="number" domain={[0, 5]} tick={{fontSize:10,fill:'#8A9E99'}} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{fontSize:11,fill:'#4A5E5A',fontWeight:600}} axisLine={false} tickLine={false} />
              <Tooltip cursor={{fill:'rgba(74,144,136,.04)'}} contentStyle={{background:'#FDFAF4',border:'1px solid rgba(13,31,30,.1)',borderRadius:10,fontSize:12}} />
              <Bar dataKey="avgScore" name="Avg Score" fill="#2E6B60" radius={[0,4,4,0]} barSize={24} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Trend Line */}
        <div className={`${styles.card} ${styles.span4}`}>
          <div className={styles.cardHeader}>
            <div className={styles.cardTitle}>📈 College Trend</div>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(13,31,30,.06)" />
              <XAxis dataKey="term" tick={{fontSize:10,fill:'#8A9E99'}} axisLine={false} tickLine={false} />
              <YAxis domain={[3, 4]} tick={{fontSize:10,fill:'#8A9E99'}} axisLine={false} tickLine={false} width={30}/>
              <Tooltip contentStyle={{background:'#FDFAF4',border:'1px solid rgba(13,31,30,.1)',borderRadius:10,fontSize:12}} />
              <Line type="monotone" dataKey="score" stroke="#C9954A" strokeWidth={3} dot={{ r: 5, fill: '#C9954A', strokeWidth: 2, stroke: '#fff' }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Dept Band Breakdown */}
        <div className={`${styles.card} ${styles.span12}`}>
          <div className={styles.cardHeader}>
            <div className={styles.cardTitle}>🎯 Department Band Breakdown</div>
          </div>
          <div className={styles.tableWrap}>
            <table>
              <thead>
                <tr>
                  <th>Department</th>
                  <th>Total Faculty</th>
                  <th>Avg Score</th>
                  <th>Strong (≥4.0)</th>
                  <th>Developing (3.0-3.9)</th>
                  <th>Needs Support (&lt;3.0)</th>
                </tr>
              </thead>
              <tbody>
                {deptData.map(d => (
                  <tr key={d.name}>
                    <td style={{fontWeight:700, color:'#0D1F1E'}}>{d.name}</td>
                    <td>{d.count}</td>
                    <td><strong style={{color: d.avgScore >= 3.5 ? '#1E6F4A' : '#9C7423'}}>{d.avgScore.toFixed(2)}</strong></td>
                    <td><span className={styles.badge} style={{background:'#E0F5EB',color:'#1E6F4A'}}>{d.strong}</span></td>
                    <td><span className={styles.badge} style={{background:'#F3E9D3',color:'#9C7423'}}>{d.developing}</span></td>
                    <td><span className={styles.badge} style={{background: d.needs > 0 ? '#F4DDD8' : 'rgba(13,31,30,.05)',color: d.needs > 0 ? '#9A3C2C' : '#8A9E99'}}>{d.needs}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
}
