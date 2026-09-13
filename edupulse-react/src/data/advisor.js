// ── AI Advisor ──────────────────────────────────────────────────
const COURSES = {
  clarity: [
    { name: 'Speak English Professionally: In Person, Online & On the Phone', provider: 'Coursera', institution: 'Georgia Tech', duration: '16h', url: 'https://www.coursera.org/learn/speak-english-professionally', match: 'Clarity & Explanation Skills' },
    { name: 'Effective Engineering Teaching in Practice', provider: 'NPTEL', institution: 'IIT Bombay', duration: '12 weeks', url: 'https://nptel.ac.in/courses/122104015', match: 'Pedagogical Clarity' },
    { name: 'Becoming a more versatile learner', provider: 'MIT OCW', institution: 'MIT', duration: 'Self-paced', url: 'https://ocw.mit.edu', match: 'Teaching Clarity' },
  ],
  methodology: [
    { name: 'Foundations of Teaching for Learning: Being a Teacher', provider: 'Coursera', institution: 'Commonwealth Edu. Trust', duration: '20h', url: 'https://www.coursera.org/learn/teaching', match: 'Teaching Methodology' },
    { name: 'Pedagogy for Online Teaching', provider: 'NPTEL', institution: 'IIT Madras', duration: '8 weeks', url: 'https://nptel.ac.in/courses/122106086', match: 'Methodology Diversity' },
    { name: 'Science of Learning: What Every Teacher Should Know', provider: 'edX', institution: 'Columbia Univ.', duration: '6 weeks', url: 'https://www.edx.org', match: 'Evidence-Based Teaching' },
  ],
  fairness: [
    { name: 'Assessment for Learning', provider: 'Coursera', institution: 'Univ. of London', duration: '10h', url: 'https://www.coursera.org/learn/assessment-for-learning', match: 'Fair Assessment Design' },
    { name: 'Designing Learner-Centric MOOCs', provider: 'NPTEL', institution: 'IIT Bombay', duration: '8 weeks', url: 'https://nptel.ac.in/courses/122104016', match: 'Transparent Evaluation' },
  ],
  approachability: [
    { name: 'Inspiring and Motivating Individuals', provider: 'Coursera', institution: 'Univ. of Michigan', duration: '8h', url: 'https://www.coursera.org/learn/motivate-people-teams', match: 'Student Motivation' },
    { name: 'Coaching and Mentoring', provider: 'LinkedIn', institution: 'LinkedIn Learning', duration: '4h', url: 'https://www.linkedin.com/learning/coaching-and-mentoring', match: 'Mentoring Skills' },
  ],
  pacing: [
    { name: 'Learning How to Learn: Powerful mental tools', provider: 'Coursera', institution: 'UC San Diego', duration: '15h', url: 'https://www.coursera.org/learn/learning-how-to-learn', match: 'Cognitive Load & Syllabus Pacing' },
    { name: 'Curriculum Design', provider: 'NPTEL', institution: 'IIT Kanpur', duration: '6 weeks', url: 'https://nptel.ac.in/courses/122104014', match: 'Curriculum Planning & Pacing' },
  ],
  punctuality: [
    { name: 'Work Smarter, Not Harder: Time Management', provider: 'Coursera', institution: 'UC Irvine', duration: '6h', url: 'https://www.coursera.org/learn/work-smarter-not-harder', match: 'Schedule Adherence' },
    { name: 'Time Management Fundamentals', provider: 'LinkedIn', institution: 'LinkedIn Learning', duration: '3h', url: 'https://www.linkedin.com/learning/time-management-fundamentals', match: 'Punctuality & Planning' },
  ],
  engagement: [
    { name: 'Active Learning in STEM: Motivating and Engaging Students', provider: 'Coursera', institution: 'MIT MITx', duration: '8h', url: 'https://www.coursera.org/learn/active-learning-in-stem', match: 'Classroom Interaction' },
    { name: 'Developing Soft Skills and Personality', provider: 'NPTEL', institution: 'IIT Kanpur', duration: '12 weeks', url: 'https://nptel.ac.in/courses/109104092', match: 'Engagement Skills' },
  ],
  overall: [
    { name: 'Foundations of Teaching for Learning', provider: 'Coursera', institution: 'Commonwealth Edu. Trust', duration: '20h', url: 'https://www.coursera.org/learn/teaching', match: 'Holistic Excellence' },
  ],
};

const TASK_PLANS = {
  clarity: {
    title: 'Clarity Improvement Plan',
    weeks: [
      { week: 'Week 1', phase: 'Diagnose', color: '#1E6F4A', tasks: ['Record one class session and self-review your explanation style', 'List the 5 concepts students find most confusing', 'Read one article on the Feynman Technique for clear teaching'] },
      { week: 'Week 2', phase: 'Restructure', color: '#C9954A', tasks: ['Rewrite explanations for top-5 confusing topics using simpler language', 'Create a glossary sheet for technical terms used in class', 'Introduce one analogy or story per concept this week'] },
      { week: 'Week 3', phase: 'Practice', color: '#2E6B60', tasks: ['Use a 5-min "check for understanding" activity at each class end', 'Pilot teaching a concept using diagram + verbal + example triad', 'Ask a colleague to observe one class and give structured feedback'] },
      { week: 'Week 4', phase: 'Evaluate', color: '#9A4E2C', tasks: ['Conduct an informal 3-question clarity poll with students', 'Review results and identify still-unclear topic areas', 'Set one measurable clarity goal for next month'] },
    ],
  },
  methodology: {
    title: 'Teaching Methods Upgrade Plan',
    weeks: [
      { week: 'Week 1', phase: 'Explore', color: '#1E6F4A', tasks: ['Research 3 active learning techniques (Think-Pair-Share, Flipped Classroom, Case Study)', "Watch 2 NPTEL sample lectures for methodology inspiration", "Map your current technique to Bloom's Taxonomy levels"] },
      { week: 'Week 2', phase: 'Design', color: '#C9954A', tasks: ['Design one lesson using the 5E model (Engage, Explore, Explain, Elaborate, Evaluate)', 'Create at least one visual aid (flowchart, diagram) for a complex topic', 'Plan one problem-based learning activity for the week'] },
      { week: 'Week 3', phase: 'Implement', color: '#2E6B60', tasks: ['Deliver one class using the redesigned lesson plan', 'Use one multimedia element (video, simulation, or tool) in class', 'Encourage at least 3 student questions per session'] },
      { week: 'Week 4', phase: 'Reflect', color: '#9A4E2C', tasks: ['Compare student engagement and performance vs. previous weeks', 'Ask students to describe one session using 3 words', 'Document what worked and create an improvement plan for next month'] },
    ],
  },
  fairness: {
    title: 'Fair Assessment Practice Plan',
    weeks: [
      { week: 'Week 1', phase: 'Audit', color: '#1E6F4A', tasks: ['Review your last assessment rubric for clarity and transparency', 'Check if marking scheme was shared with students before the test', 'Read UGC guidelines on fair and transparent assessment'] },
      { week: 'Week 2', phase: 'Design', color: '#C9954A', tasks: ['Create a detailed marking rubric for your next internal assessment', 'Map each question to specific learning outcomes', 'Establish a written policy for revaluation requests'] },
      { week: 'Week 3', phase: 'Communicate', color: '#2E6B60', tasks: ['Share the marking rubric with students before the test', 'Discuss model answers after assessment completion', 'Implement a structured feedback format for returned papers'] },
      { week: 'Week 4', phase: 'Review', color: '#9A4E2C', tasks: ['Survey 5 students on their perception of assessment fairness', 'Review grade distribution for consistency and outliers', 'Document and refine your assessment process for next term'] },
    ],
  },
  approachability: {
    title: 'Student Mentoring & Approachability Plan',
    weeks: [
      { week: 'Week 1', phase: 'Open Up', color: '#1E6F4A', tasks: ['Establish published office hours (at least 2 hours/week)', 'Create a WhatsApp group or email channel for student queries', 'Introduce yourself as approachable in the very next class session'] },
      { week: 'Week 2', phase: 'Reach Out', color: '#C9954A', tasks: ['Proactively check in with 3 students who seem disengaged', 'Hold one open Q&A session at the end of this week', 'Commit to responding to all student messages within 24 hours'] },
      { week: 'Week 3', phase: 'Deepen', color: '#2E6B60', tasks: ['Conduct 5-min one-on-one check-ins with struggling students', 'Share study resources proactively (notes, references, links)', 'Run a 10-min anonymous concerns activity in class'] },
      { week: 'Week 4', phase: 'Sustain', color: '#9A4E2C', tasks: ['Review frequency of student interactions — are you accessible enough?', 'Set up a recurring weekly "drop-in" session format', 'Measure comfort level improvement through informal conversations'] },
    ],
  },
  pacing: {
    title: 'Syllabus Pacing & Planning Plan',
    weeks: [
      { week: 'Week 1', phase: 'Map', color: '#1E6F4A', tasks: ['Create a detailed week-by-week syllabus delivery timeline', 'Identify which topics are most time-intensive or complex', 'Review past semesters — where did the pace rush happen?'] },
      { week: 'Week 2', phase: 'Structure', color: '#C9954A', tasks: ['Build in 2 buffer weeks for revision/catch-up in your plan', 'Create "spaced repetition" checkpoints every 3 weeks', 'Identify 2 topics suitable for guided self-study with your support'] },
      { week: 'Week 3', phase: 'Monitor', color: '#2E6B60', tasks: ['Check plan vs actual progress every Friday', 'If behind: identify what to accelerate without quality loss', 'Share pacing progress with students so they can plan too'] },
      { week: 'Week 4', phase: 'Calibrate', color: '#9A4E2C', tasks: ['Run a poll: "Are we covering content at the right pace?"', 'Adjust next month\'s plan based on student feedback', 'Document a pacing template for the next semester'] },
    ],
  },
  engagement: {
    title: 'Classroom Engagement Boost Plan',
    weeks: [
      { week: 'Week 1', phase: 'Baseline', color: '#1E6F4A', tasks: ['Count how many students participate voluntarily in a typical class', 'Identify 3 "quiet students" and make a note to engage them', 'Research 2 gamification techniques for classroom engagement'] },
      { week: 'Week 2', phase: 'Activate', color: '#C9954A', tasks: ['Start each class with a 5-min warm-up question or mini-quiz', 'Use Think-Pair-Share for at least one topic per week', 'Address students by name when calling on them to respond'] },
      { week: 'Week 3', phase: 'Energize', color: '#2E6B60', tasks: ['Run one group problem-solving activity this week', 'Use Mentimeter or similar for live polls if technology is available', 'Give "exit tickets" — 2-min written summaries from students'] },
      { week: 'Week 4', phase: 'Measure', color: '#9A4E2C', tasks: ['Count participation rate — has it improved from Week 1?', 'Ask 5 students: "What made you pay most attention this month?"', 'Set 3 measurable engagement goals for the next month'] },
    ],
  },
};

export function compositeScore(scores) {
  const vals = Object.values(scores).filter(v => v > 0);
  if (!vals.length) return 0;
  return +(vals.reduce((s, v) => s + v, 0) / vals.length).toFixed(1);
}

export function scoreToBand(avg) {
  if (avg >= 4.0) return { band: 'Strong',         cls: 'strong',      icon: '🌟', color: '#1E6F4A', bg: '#E0F5EB' };
  if (avg >= 3.0) return { band: 'Developing',     cls: 'developing',  icon: '📈', color: '#9C7423', bg: '#F3E9D3' };
  return               { band: 'Needs Support',    cls: 'needs',       icon: '⚠️', color: '#9A3C2C', bg: '#F4DDD8' };
}

export function generateSuggestions(fac) {
  const weakDims = Object.entries(fac.scores)
    .filter(([, v]) => v < 3.5)
    .sort((a, b) => a[1] - b[1])
    .slice(0, 3)
    .map(([d]) => d);

  if (!weakDims.length) {
    return { needsImprovement: false, message: `${fac.name} is performing strongly across all teaching dimensions. Keep up the excellent work!`, courses: [], taskPlan: null, weakDims: [] };
  }

  const courses = [];
  const seen = new Set();
  weakDims.forEach(d => {
    const cat = COURSES[d] || COURSES.overall;
    if (!seen.has(d)) { courses.push(...cat.slice(0, 2)); seen.add(d); }
  });

  const primaryWeak = weakDims[0];
  const taskPlan = TASK_PLANS[primaryWeak] || TASK_PLANS.engagement;
  const avg = compositeScore(fac.scores);
  const band = scoreToBand(avg);
  const dimLabels = { clarity:'clarity', methodology:'teaching methodology', fairness:'assessment fairness', approachability:'approachability', pacing:'syllabus pacing', engagement:'classroom engagement', practical:'practical sessions', assessment:'assessment design', overall:'overall effectiveness' };
  const weakStr = weakDims.map(d => dimLabels[d] || d).join(', ');

  return {
    needsImprovement: true,
    weakDims,
    primaryWeak,
    message: `Student feedback highlights ${weakStr} as primary areas needing attention. Overall band: ${band.band} (${avg}/5). A personalized development pathway has been curated below.`,
    courses: courses.slice(0, 6),
    taskPlan,
  };
}
