// ── Question Engine ─────────────────────────────────────────────
// Adaptive branching: negative answer → inject sub-question
// Always shows exactly 10 questions total

export const MAIN_QUESTIONS = [
  {
    id: 'q_clarity', dim: 'clarity',
    text: 'How clearly does the faculty explain concepts and topics in class?',
    options: [
      { value: 4, label: 'Excellent',         icon: '🌟', mood: 'excellent', desc: 'Crystal clear, always easy to follow' },
      { value: 3, label: 'Good',              icon: '👍', mood: 'good',      desc: 'Mostly clear with minor gaps' },
      { value: 2, label: 'Needs Improvement', icon: '😐', mood: 'fair',      desc: 'Often confusing or hard to follow' },
      { value: 1, label: 'Poor',              icon: '👎', mood: 'poor',      desc: 'Very unclear, difficult to understand' },
    ],
  },
  {
    id: 'q_methodology', dim: 'methodology',
    text: 'Does the faculty use effective and engaging teaching methods?',
    options: [
      { value: 4, label: 'Excellent',         icon: '🌟', mood: 'excellent', desc: 'Creative, varied, and highly engaging' },
      { value: 3, label: 'Good',              icon: '👍', mood: 'good',      desc: 'Standard methods, reasonably effective' },
      { value: 2, label: 'Needs Improvement', icon: '😐', mood: 'fair',      desc: 'Monotonous, could be more interactive' },
      { value: 1, label: 'Poor',              icon: '👎', mood: 'poor',      desc: 'Ineffective, no engagement at all' },
    ],
  },
  {
    id: 'q_punctuality', dim: 'punctuality',
    text: 'Does the faculty conduct classes on time and complete scheduled hours?',
    options: [
      { value: 4, label: 'Excellent',         icon: '🌟', mood: 'excellent', desc: 'Always punctual, full hours conducted' },
      { value: 3, label: 'Good',              icon: '👍', mood: 'good',      desc: 'Mostly on time with rare delays' },
      { value: 2, label: 'Needs Improvement', icon: '😐', mood: 'fair',      desc: 'Frequently late or ends early' },
      { value: 1, label: 'Poor',              icon: '👎', mood: 'poor',      desc: 'Consistently misses scheduled time' },
    ],
  },
  {
    id: 'q_fairness', dim: 'fairness',
    text: 'Are internal marks and assessments awarded fairly and transparently?',
    options: [
      { value: 4, label: 'Excellent',         icon: '🌟', mood: 'excellent', desc: 'Completely fair and transparent' },
      { value: 3, label: 'Good',              icon: '👍', mood: 'good',      desc: 'Generally fair with minor concerns' },
      { value: 2, label: 'Needs Improvement', icon: '😐', mood: 'fair',      desc: 'Some inconsistency in grading' },
      { value: 1, label: 'Poor',              icon: '👎', mood: 'poor',      desc: 'Perceived bias or unfair grading' },
    ],
  },
  {
    id: 'q_approachability', dim: 'approachability',
    text: 'Is the faculty accessible and approachable for doubt-clearing outside class?',
    options: [
      { value: 4, label: 'Excellent',         icon: '🌟', mood: 'excellent', desc: 'Always available and welcoming' },
      { value: 3, label: 'Good',              icon: '👍', mood: 'good',      desc: 'Usually available with some delays' },
      { value: 2, label: 'Needs Improvement', icon: '😐', mood: 'fair',      desc: 'Rarely available outside class' },
      { value: 1, label: 'Poor',              icon: '👎', mood: 'poor',      desc: 'Never available for doubts' },
    ],
  },
  {
    id: 'q_pacing', dim: 'pacing',
    text: 'Is the syllabus covered at an appropriate pace throughout the semester?',
    options: [
      { value: 4, label: 'Excellent',         icon: '🌟', mood: 'excellent', desc: 'Perfect pacing, well planned' },
      { value: 3, label: 'Good',              icon: '👍', mood: 'good',      desc: 'Generally good with minor rush' },
      { value: 2, label: 'Needs Improvement', icon: '😐', mood: 'fair',      desc: 'Rushed at end or too slow at start' },
      { value: 1, label: 'Poor',              icon: '👎', mood: 'poor',      desc: 'Very poorly paced, incomplete coverage' },
    ],
  },
  {
    id: 'q_engagement', dim: 'engagement',
    text: 'Does the faculty encourage student participation and make classes interactive?',
    options: [
      { value: 4, label: 'Excellent',         icon: '🌟', mood: 'excellent', desc: 'Highly interactive, great participation' },
      { value: 3, label: 'Good',              icon: '👍', mood: 'good',      desc: 'Reasonably interactive' },
      { value: 2, label: 'Needs Improvement', icon: '😐', mood: 'fair',      desc: 'Mostly lecture-based, little interaction' },
      { value: 1, label: 'Poor',              icon: '👎', mood: 'poor',      desc: 'No class interaction at all' },
    ],
  },
  {
    id: 'q_practical', dim: 'practical',
    text: 'Are practical/lab sessions and demonstrations conducted effectively?',
    options: [
      { value: 4, label: 'Excellent',         icon: '🌟', mood: 'excellent', desc: 'Excellent lab sessions, well guided' },
      { value: 3, label: 'Good',              icon: '👍', mood: 'good',      desc: 'Good practical coverage' },
      { value: 2, label: 'Needs Improvement', icon: '😐', mood: 'fair',      desc: 'Inconsistent lab sessions' },
      { value: 1, label: 'Poor',              icon: '👎', mood: 'poor',      desc: 'No practical sessions conducted' },
    ],
  },
  {
    id: 'q_assessment', dim: 'assessment',
    text: 'Are assignments, tests, and question papers clear and reasonable?',
    options: [
      { value: 4, label: 'Excellent',         icon: '🌟', mood: 'excellent', desc: 'Well-designed, clear expectations' },
      { value: 3, label: 'Good',              icon: '👍', mood: 'good',      desc: 'Mostly clear with minor issues' },
      { value: 2, label: 'Needs Improvement', icon: '😐', mood: 'fair',      desc: 'Unclear questions or unreasonable difficulty' },
      { value: 1, label: 'Poor',              icon: '👎', mood: 'poor',      desc: 'Very poorly designed assessments' },
    ],
  },
  {
    id: 'q_overall', dim: 'overall',
    text: 'Overall, how would you rate this faculty member\'s teaching effectiveness?',
    options: [
      { value: 4, label: 'Excellent',         icon: '🌟', mood: 'excellent', desc: 'Outstanding teacher, highly recommend' },
      { value: 3, label: 'Good',              icon: '👍', mood: 'good',      desc: 'Good teacher overall' },
      { value: 2, label: 'Needs Improvement', icon: '😐', mood: 'fair',      desc: 'Average, has room to improve' },
      { value: 1, label: 'Poor',              icon: '👎', mood: 'poor',      desc: 'Needs significant improvement' },
    ],
  },
];

export const SUB_QUESTIONS = {
  q_clarity: [
    {
      id: 'sq_clarity_1', dim: 'clarity', isSub: true,
      text: 'Which specific aspect of explanation needs the most improvement?',
      options: [
        { value: 1, label: 'Too much jargon',   icon: '📚', mood: 'fair', desc: 'Technical terms without clear explanation' },
        { value: 2, label: 'Lacks examples',    icon: '💡', mood: 'fair', desc: 'No real-world examples to relate to' },
        { value: 3, label: 'Speed of delivery', icon: '⚡', mood: 'fair', desc: 'Speaks too fast or too slow' },
        { value: 4, label: 'Poor board/slides', icon: '📋', mood: 'fair', desc: 'Unclear writing or disorganized slides' },
      ],
    },
    {
      id: 'sq_clarity_2', dim: 'clarity', isSub: true,
      text: 'How frequently do you find yourself unable to follow the core concepts?',
      options: [
        { value: 1, label: 'Almost always',     icon: '😟', mood: 'fair', desc: 'In almost every lecture' },
        { value: 2, label: 'Frequently',        icon: '🤔', mood: 'fair', desc: 'Often enough to fall behind' },
        { value: 3, label: 'Sometimes',         icon: '😐', mood: 'fair', desc: 'Only for complex topics' },
        { value: 4, label: 'Rarely',            icon: '🙂', mood: 'fair', desc: 'I usually understand eventually' },
      ]
    },
    {
      id: 'sq_clarity_3', dim: 'clarity', isSub: true,
      text: 'What action would immediately improve your understanding?',
      options: [
        { value: 1, label: 'Pre-class notes',   icon: '📝', mood: 'fair', desc: 'Providing notes before class begins' },
        { value: 2, label: 'Step-by-step',      icon: '🪜', mood: 'fair', desc: 'Breaking down problems slower' },
        { value: 3, label: 'More analogies',    icon: '🧠', mood: 'fair', desc: 'Relating concepts to known things' },
        { value: 4, label: 'Summary at end',    icon: '🔁', mood: 'fair', desc: 'A quick recap of what was taught' },
      ]
    }
  ],
  q_methodology: [
    {
      id: 'sq_methodology_1', dim: 'methodology', isSub: true,
      text: 'What teaching method would most improve your learning experience?',
      options: [
        { value: 1, label: 'Live demonstrations', icon: '🎯', mood: 'fair', desc: 'Hands-on demonstrations in class' },
        { value: 2, label: 'Case studies',        icon: '📖', mood: 'fair', desc: 'Real-world case studies and examples' },
        { value: 3, label: 'Group activities',    icon: '👥', mood: 'fair', desc: 'Collaborative problem solving' },
        { value: 4, label: 'Visual / multimedia', icon: '🖼️', mood: 'fair', desc: 'Videos, diagrams, simulations' },
      ],
    },
    {
      id: 'sq_methodology_2', dim: 'methodology', isSub: true,
      text: 'How would you describe the current lecture style?',
      options: [
        { value: 1, label: 'Pure dictation',      icon: '✍️', mood: 'fair', desc: 'Just reading notes aloud' },
        { value: 2, label: 'Slide reading',       icon: '💻', mood: 'fair', desc: 'Reading directly from presentations' },
        { value: 3, label: 'Monotonous',          icon: '🥱', mood: 'fair', desc: 'Lacks energy or variety' },
        { value: 4, label: 'Disorganized',        icon: '🌪️', mood: 'fair', desc: 'Jumps between topics randomly' },
      ]
    },
    {
      id: 'sq_methodology_3', dim: 'methodology', isSub: true,
      text: 'Which type of material helps you learn best?',
      options: [
        { value: 1, label: 'Visual Aids',         icon: '📊', mood: 'fair', desc: 'Charts, mind-maps, diagrams' },
        { value: 2, label: 'Practical tasks',     icon: '🛠️', mood: 'fair', desc: 'Doing it rather than hearing it' },
        { value: 3, label: 'Written materials',   icon: '📑', mood: 'fair', desc: 'Comprehensive textbooks or handouts' },
        { value: 4, label: 'Interactive tech',    icon: '📱', mood: 'fair', desc: 'Simulations and educational software' },
      ]
    }
  ],
  q_punctuality: [
    {
      id: 'sq_punctuality_1', dim: 'punctuality', isSub: true,
      text: 'How does the punctuality issue most affect you?',
      options: [
        { value: 1, label: 'Late starts',       icon: '⏰', mood: 'fair', desc: 'Classes begin significantly after schedule' },
        { value: 2, label: 'Early endings',     icon: '🏃', mood: 'fair', desc: 'Classes end before the scheduled time' },
        { value: 3, label: 'Cancelled classes', icon: '❌', mood: 'fair', desc: 'Frequent class cancellations' },
        { value: 4, label: 'No fixed schedule', icon: '📅', mood: 'fair', desc: 'Unpredictable schedule maintained' },
      ],
    },
    {
      id: 'sq_punctuality_2', dim: 'punctuality', isSub: true,
      text: 'On average, how much class time is lost per session?',
      options: [
        { value: 1, label: '15+ minutes',       icon: '⌛', mood: 'fair', desc: 'Significant portion of the class' },
        { value: 2, label: '10-15 minutes',     icon: '⏱️', mood: 'fair', desc: 'Noticeable delay' },
        { value: 3, label: '5-10 minutes',      icon: '⏳', mood: 'fair', desc: 'Slight delay' },
        { value: 4, label: 'Irregular',         icon: '🤷', mood: 'fair', desc: 'Varies drastically day by day' },
      ]
    },
    {
      id: 'sq_punctuality_3', dim: 'punctuality', isSub: true,
      text: 'Are missed classes adequately compensated?',
      options: [
        { value: 1, label: 'Never',             icon: '🚫', mood: 'fair', desc: 'No makeup classes held' },
        { value: 2, label: 'Rarely',            icon: '📉', mood: 'fair', desc: 'Only right before exams' },
        { value: 3, label: 'Sometimes',         icon: '⚖️', mood: 'fair', desc: 'Makeup classes are held but poorly timed' },
        { value: 4, label: 'Always',            icon: '✅', mood: 'fair', desc: 'Yes, but the pacing feels rushed' },
      ]
    }
  ],
  q_fairness: [
    {
      id: 'sq_fairness_1', dim: 'fairness', isSub: true,
      text: 'Which aspect of assessment fairness concerns you most?',
      options: [
        { value: 1, label: 'No feedback given',     icon: '📝', mood: 'fair', desc: 'Scores given without explanation' },
        { value: 2, label: 'Inconsistent grading',  icon: '⚖️', mood: 'fair', desc: 'Different standards for different students' },
        { value: 3, label: 'Out-of-syllabus Qs',    icon: '😰', mood: 'fair', desc: 'Questions outside syllabus scope' },
        { value: 4, label: 'No rechecking option',  icon: '🔍', mood: 'fair', desc: 'Cannot request mark review' },
      ],
    },
    {
      id: 'sq_fairness_2', dim: 'fairness', isSub: true,
      text: 'How transparent is the evaluation scheme before tests?',
      options: [
        { value: 1, label: 'No scheme shared',      icon: '🙈', mood: 'fair', desc: 'Never know how we will be marked' },
        { value: 2, label: 'Vague criteria',        icon: '🌫️', mood: 'fair', desc: 'Criteria are unclear or ambiguous' },
        { value: 3, label: 'Changed mid-way',       icon: '🔄', mood: 'fair', desc: 'Rules change after submission' },
        { value: 4, label: 'Only told afterwards',  icon: '🔙', mood: 'fair', desc: 'Scheme revealed only with results' },
      ]
    },
    {
      id: 'sq_fairness_3', dim: 'fairness', isSub: true,
      text: 'Do you feel comfortable discussing your grades with this faculty?',
      options: [
        { value: 1, label: 'Not at all',            icon: '🛑', mood: 'fair', desc: 'Afraid of retaliation or anger' },
        { value: 2, label: 'Dismissive attitude',   icon: '😒', mood: 'fair', desc: 'Faculty won\'t listen to concerns' },
        { value: 3, label: 'Only via email',        icon: '📧', mood: 'fair', desc: 'Face-to-face is discouraged' },
        { value: 4, label: 'Yes, but unhelpful',    icon: '🤷', mood: 'fair', desc: 'Can discuss but grades never change' },
      ]
    }
  ],
  q_approachability: [
    {
      id: 'sq_approachability_1', dim: 'approachability', isSub: true,
      text: 'What is the main barrier in approaching this faculty?',
      options: [
        { value: 1, label: 'Never in office hours',   icon: '🚪', mood: 'fair', desc: 'Not available during office hours' },
        { value: 2, label: 'Discourages questions',   icon: '🤫', mood: 'fair', desc: 'Makes students feel unwelcome' },
        { value: 3, label: 'Slow response to queries',icon: '📱', mood: 'fair', desc: 'Takes days to respond' },
        { value: 4, label: 'No online support',       icon: '💻', mood: 'fair', desc: 'No email or portal support' },
      ],
    },
    {
      id: 'sq_approachability_2', dim: 'approachability', isSub: true,
      text: 'How does the faculty react to questions during class?',
      options: [
        { value: 1, label: 'Gets angry/annoyed',      icon: '😠', mood: 'fair', desc: 'Hostile response to interruptions' },
        { value: 2, label: 'Mocks the student',       icon: '🤡', mood: 'fair', desc: 'Belittles the person asking' },
        { value: 3, label: 'Defers to later',         icon: '⏭️', mood: 'fair', desc: 'Says "we\'ll cover it later" but doesn\'t' },
        { value: 4, label: 'Rushes the answer',       icon: '💨', mood: 'fair', desc: 'Gives a very brief, unhelpful reply' },
      ]
    },
    {
      id: 'sq_approachability_3', dim: 'approachability', isSub: true,
      text: 'What would make you feel more comfortable asking for help?',
      options: [
        { value: 1, label: 'Fixed open-door times',   icon: '🗓️', mood: 'fair', desc: 'Guaranteed availability hours' },
        { value: 2, label: 'Anonymous Q&A box',       icon: '🗳️', mood: 'fair', desc: 'Ability to ask without being named' },
        { value: 3, label: 'Dedicated TA sessions',   icon: '🧑‍🏫', mood: 'fair', desc: 'Approaching a teaching assistant instead' },
        { value: 4, label: 'A friendlier tone',       icon: '😊', mood: 'fair', desc: 'Just being more welcoming overall' },
      ]
    }
  ],
  q_pacing: [
    {
      id: 'sq_pacing_1', dim: 'pacing', isSub: true,
      text: 'How does the pacing problem mainly affect this course?',
      options: [
        { value: 1, label: 'Rushed at semester end', icon: '🏁', mood: 'fair', desc: 'Too fast in the final weeks' },
        { value: 2, label: 'Too slow at start',      icon: '🐢', mood: 'fair', desc: 'Too much time on early topics' },
        { value: 3, label: 'Topics skipped',         icon: '⏭️', mood: 'fair', desc: 'Important topics are left out' },
        { value: 4, label: 'Repetitive content',     icon: '🔁', mood: 'fair', desc: 'Same topics covered repeatedly' },
      ],
    },
    {
      id: 'sq_pacing_2', dim: 'pacing', isSub: true,
      text: 'Is the course syllabus completed before exams?',
      options: [
        { value: 1, label: 'Not even close',         icon: '📉', mood: 'fair', desc: 'Major portions left out' },
        { value: 2, label: 'Self-study assigned',    icon: '📚', mood: 'fair', desc: 'Told to read the rest ourselves' },
        { value: 3, label: 'Rushed completion',      icon: '🌪️', mood: 'fair', desc: 'Finished in a 4-hour marathon class' },
        { value: 4, label: 'Only partially',         icon: '🧩', mood: 'fair', desc: 'Missing one or two modules' },
      ]
    },
    {
      id: 'sq_pacing_3', dim: 'pacing', isSub: true,
      text: 'How well does the pacing match the difficulty of topics?',
      options: [
        { value: 1, label: 'Fast on hard topics',    icon: '⚡', mood: 'fair', desc: 'Complex stuff is rushed' },
        { value: 2, label: 'Slow on easy topics',    icon: '🐌', mood: 'fair', desc: 'Wastes time on basics' },
        { value: 3, label: 'No logical flow',        icon: '🔀', mood: 'fair', desc: 'Jumps between hard and easy randomly' },
        { value: 4, label: 'No time for practice',   icon: '🚫', mood: 'fair', desc: 'Theory is fine, but no time for problems' },
      ]
    }
  ],
  q_engagement: [
    {
      id: 'sq_engagement_1', dim: 'engagement', isSub: true,
      text: 'What would make classes more engaging for you?',
      options: [
        { value: 1, label: 'Q&A sessions',    icon: '🙋', mood: 'fair', desc: 'Regular question-answer sessions' },
        { value: 2, label: 'In-class quizzes',icon: '📊', mood: 'fair', desc: 'Quizzes and polls during class' },
        { value: 3, label: 'Industry connect',icon: '🏢', mood: 'fair', desc: 'Guest lectures, industry examples' },
        { value: 4, label: 'Mini-projects',   icon: '🔨', mood: 'fair', desc: 'Hands-on project work' },
      ],
    },
    {
      id: 'sq_engagement_2', dim: 'engagement', isSub: true,
      text: 'Are students encouraged to share their opinions or solutions?',
      options: [
        { value: 1, label: 'Never',           icon: '🤐', mood: 'fair', desc: 'Strictly one-way lecture' },
        { value: 2, label: 'Only top students',icon: '⭐', mood: 'fair', desc: 'Only engages with a select few' },
        { value: 3, label: 'Rarely',          icon: '📉', mood: 'fair', desc: 'Only if there is extra time' },
        { value: 4, label: 'Dismissed',       icon: '👎', mood: 'fair', desc: 'Student input is ignored or dismissed' },
      ]
    },
    {
      id: 'sq_engagement_3', dim: 'engagement', isSub: true,
      text: 'How is the energy level of the faculty during class?',
      options: [
        { value: 1, label: 'Very low/Boring', icon: '😴', mood: 'fair', desc: 'Puts people to sleep' },
        { value: 2, label: 'Distracted',      icon: '📱', mood: 'fair', desc: 'Seems uninterested in teaching' },
        { value: 3, label: 'Strict/Tense',    icon: '😠', mood: 'fair', desc: 'Creates a stressful atmosphere' },
        { value: 4, label: 'Inconsistent',    icon: '🎢', mood: 'fair', desc: 'Varies highly from day to day' },
      ]
    }
  ],
  q_practical: [
    {
      id: 'sq_practical_1', dim: 'practical', isSub: true,
      text: 'What is the main issue with practical/lab sessions?',
      options: [
        { value: 1, label: 'No faculty demo',   icon: '🔬', mood: 'fair', desc: 'Faculty does not demonstrate steps' },
        { value: 2, label: 'Equipment issues',  icon: '🔧', mood: 'fair', desc: 'Lab equipment not working properly' },
        { value: 3, label: 'Too theoretical',   icon: '📚', mood: 'fair', desc: 'Lab sessions not hands-on enough' },
        { value: 4, label: 'Poor supervision',  icon: '👀', mood: 'fair', desc: 'Faculty not present to guide students' },
      ],
    },
    {
      id: 'sq_practical_2', dim: 'practical', isSub: true,
      text: 'Is the lab manual or instructions clear enough?',
      options: [
        { value: 1, label: 'No manual provided',icon: '🚫', mood: 'fair', desc: 'We have to figure it out ourselves' },
        { value: 2, label: 'Outdated manual',   icon: '📜', mood: 'fair', desc: 'Instructions don\'t match the software/hardware' },
        { value: 3, label: 'Too vague',         icon: '🌫️', mood: 'fair', desc: 'Missing crucial steps' },
        { value: 4, label: 'Copied from web',   icon: '🌐', mood: 'fair', desc: 'Generic instructions, not specific to our lab' },
      ]
    },
    {
      id: 'sq_practical_3', dim: 'practical', isSub: true,
      text: 'How is the lab evaluation process handled?',
      options: [
        { value: 1, label: 'Arbitrary grading', icon: '🎲', mood: 'fair', desc: 'Marks seem random' },
        { value: 2, label: 'Too harsh',         icon: '😠', mood: 'fair', desc: 'Unreasonable expectations for the time given' },
        { value: 3, label: 'No viva/questions', icon: '🤐', mood: 'fair', desc: 'Just checks output, doesn\'t check understanding' },
        { value: 4, label: 'Only checks records',icon: '📓', mood: 'fair', desc: 'More focus on writing than actual work' },
      ]
    }
  ],
  q_assessment: [
    {
      id: 'sq_assessment_1', dim: 'assessment', isSub: true,
      text: 'What aspect of assessment design needs the most improvement?',
      options: [
        { value: 1, label: 'Ambiguous questions', icon: '❓', mood: 'fair', desc: 'Test questions are unclear or vague' },
        { value: 2, label: 'Too difficult',        icon: '😓', mood: 'fair', desc: 'Difficulty level is unreasonable' },
        { value: 3, label: 'No feedback given',    icon: '💬', mood: 'fair', desc: 'No feedback on submitted work' },
        { value: 4, label: 'Time pressure',        icon: '⏱️', mood: 'fair', desc: 'Too much to do in too little time' },
      ],
    },
    {
      id: 'sq_assessment_2', dim: 'assessment', isSub: true,
      text: 'Are assignments helpful for your learning?',
      options: [
        { value: 1, label: 'Just copy-paste',     icon: '📋', mood: 'fair', desc: 'Busywork with no learning value' },
        { value: 2, label: 'Too lengthy',         icon: '📚', mood: 'fair', desc: 'Takes too much time for too few marks' },
        { value: 3, label: 'Irrelevant topics',   icon: '🔀', mood: 'fair', desc: 'Not related to what was taught' },
        { value: 4, label: 'Unclear expectations',icon: '🌫️', mood: 'fair', desc: 'Don\'t know what is required' },
      ]
    },
    {
      id: 'sq_assessment_3', dim: 'assessment', isSub: true,
      text: 'How is the difficulty level of the internal exams compared to university exams?',
      options: [
        { value: 1, label: 'Way harder',          icon: '🌋', mood: 'fair', desc: 'Unrealistically difficult' },
        { value: 2, label: 'Way easier',          icon: '🏖️', mood: 'fair', desc: 'Doesn\'t prepare us for finals' },
        { value: 3, label: 'Different format',    icon: '🔄', mood: 'fair', desc: 'Question styles don\'t match finals' },
        { value: 4, label: 'Unpredictable',       icon: '🎲', mood: 'fair', desc: 'Changes wildly every test' },
      ]
    }
  ],
  q_overall: [
    {
      id: 'sq_overall_1', dim: 'overall', isSub: true,
      text: 'What is the primary area where this faculty needs to improve most?',
      options: [
        { value: 1, label: 'Core teaching',    icon: '📖', mood: 'fair', desc: 'Teaching and explanation skills' },
        { value: 2, label: 'Student support',  icon: '🤝', mood: 'fair', desc: 'Support and mentoring outside class' },
        { value: 3, label: 'Content coverage', icon: '📋', mood: 'fair', desc: 'Syllabus and material coverage' },
        { value: 4, label: 'Assessment design',icon: '📝', mood: 'fair', desc: 'Tests and evaluation methods' },
      ],
    },
    {
      id: 'sq_overall_2', dim: 'overall', isSub: true,
      text: 'Would you recommend this faculty to a junior?',
      options: [
        { value: 1, label: 'Absolutely not',   icon: '🚫', mood: 'fair', desc: 'Would actively warn them' },
        { value: 2, label: 'Probably not',     icon: '👎', mood: 'fair', desc: 'Only if there is no other choice' },
        { value: 3, label: 'Neutral',          icon: '😐', mood: 'fair', desc: 'They are okay, nothing special' },
        { value: 4, label: 'Yes, but...',      icon: '😬', mood: 'fair', desc: 'Yes, but they need to improve some things' },
      ]
    },
    {
      id: 'sq_overall_3', dim: 'overall', isSub: true,
      text: 'What is the ONE thing you wish this faculty would change tomorrow?',
      options: [
        { value: 1, label: 'Be more respectful',icon: '🙏', mood: 'fair', desc: 'Treat students better' },
        { value: 2, label: 'Prepare better',    icon: '📚', mood: 'fair', desc: 'Come to class with a clear plan' },
        { value: 3, label: 'Grade fairly',      icon: '⚖️', mood: 'fair', desc: 'Stop biased or arbitrary grading' },
        { value: 4, label: 'Slow down',         icon: '🐢', mood: 'fair', desc: 'Reduce the pacing of the lectures' },
      ]
    }
  ],
};

/** Build the adaptive question sequence (always 10 questions) */
export function buildSession() {
  return {
    queue: [...MAIN_QUESTIONS],   // remaining questions to show
    shown: [],                    // questions already answered
    answers: {},                  // { questionId: { value, label, dim, isSub } }
    done: false,
  };
}

export function isNegative(value) { return value <= 2; }

/**
 * Answer current question; returns the updated session.
 * If negative and sub-question exists and we haven't used it,
 * injects sub-questions next and removes last main questions to keep total 10.
 */
/**
 * For sub-questions: value may be an array of selected option values.
 * For main questions: value is a single number.
 */
export function answerQuestion(session, questionId, value, label, otherText = '') {
  const [current, ...rest] = session.queue;
  const answers = {
    ...session.answers,
    [questionId]: {
      value,
      label,
      otherText: otherText || null,
      dim: current.dim,
      isSub: !!current.isSub,
    },
  };
  const shown = [...session.shown, current];

  let newQueue = [...rest];

  // For main questions: inject sub-questions on negative answer
  const mainValue = Array.isArray(value) ? Math.min(...value) : value;
  if (!current.isSub && isNegative(mainValue)) {
    const subs = SUB_QUESTIONS[current.id];
    if (subs && subs.length > 0) {
      const firstSubId = subs[0].id;
      if (!answers[firstSubId] && !newQueue.find(q => q.id === firstSubId)) {
        newQueue = [...subs, ...newQueue];
        let toRemove = subs.length;
        for (let i = newQueue.length - 1; i >= 0 && toRemove > 0; i--) {
          if (!newQueue[i].isSub) {
            newQueue.splice(i, 1);
            toRemove--;
          }
        }
      }
    }
  }

  const done = newQueue.length === 0 || shown.length >= 10;

  return {
    queue: done ? [] : newQueue,
    shown,
    answers,
    done,
  };
}

/**
 * Compute raw 1-4 integer scores per dimension for backend submission.
 * Sub-question answers are excluded from scoring.
 */
export function computeScores(answers) {
  const dimMap = {};
  Object.values(answers).forEach(({ dim, value, isSub }) => {
    if (isSub) return;
    if (!dimMap[dim]) dimMap[dim] = [];
    const v = Array.isArray(value) ? value[0] : value; // use first if multi
    dimMap[dim].push(v);
  });
  const scores = {};
  Object.entries(dimMap).forEach(([dim, vals]) => {
    const avg = vals.reduce((s, v) => s + v, 0) / vals.length;
    // Keep as 1-4 int for backend schema compliance
    scores[dim] = Math.min(4, Math.max(1, Math.round(avg)));
  });
  return scores;
}

/**
 * Compute display scores (1-5 scale) for UI presentation.
 */
export function computeScoresDisplay(answers) {
  const dimMap = {};
  Object.values(answers).forEach(({ dim, value, isSub }) => {
    if (isSub) return;
    if (!dimMap[dim]) dimMap[dim] = [];
    const v = Array.isArray(value) ? value[0] : value;
    dimMap[dim].push(v);
  });
  const scores = {};
  Object.entries(dimMap).forEach(([dim, vals]) => {
    const raw = vals.reduce((s, v) => s + v, 0) / vals.length;
    scores[dim] = +((raw - 1) / 3 * 4 + 1).toFixed(2); // 1-4 → 1-5
  });
  return scores;
}
