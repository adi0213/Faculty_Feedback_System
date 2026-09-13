/**
 * EduPulse Frontend API Client — connected to FastAPI Backend v2 (/api/v2)
 */

const getApiUrl = () => {
  if (typeof import.meta !== 'undefined' && import.meta.env) {
    // Support both VITE_API_BASE_URL and legacy VITE_API_URL
    const envUrl = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL;
    if (envUrl) return envUrl;
  }
  const host = (typeof window !== 'undefined' && window.location && window.location.hostname === '127.0.0.1') ? '127.0.0.1' : 'localhost';
  return `http://${host}:8000/api/v2`;
};

const getToken = () => localStorage.getItem('edupulse_token');

const getHeaders = () => {
  const token = getToken();
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  };
};

export const DB = {
  // ── Authentication ──────────────────────────────────────────────────────────
  login: async (email, password) => {
    const baseUrl = getApiUrl();
    try {
      const res = await fetch(`${baseUrl}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || err.detail || 'Invalid email or password.');
      }
      const data = await res.json();
      localStorage.setItem('edupulse_token', data.access_token);

      // Fetch authenticated user profile
      const meRes = await fetch(`${baseUrl}/auth/me`, { headers: getHeaders() });
      if (!meRes.ok) throw new Error('Failed to fetch user profile.');
      const user = await meRes.json();

      localStorage.setItem('edupulse_session', JSON.stringify(user));
      return user;
    } catch (e) {
      console.error('Login error:', e);
      if (e.name === 'TypeError' || e.message.includes('fetch') || e.message.includes('NetworkError') || e.message.includes('Failed to fetch')) {
        throw new Error(`Backend server is offline or unreachable at ${baseUrl}. Please ensure the backend server is running.`);
      }
      throw e;
    }
  },

  logout: () => {
    localStorage.removeItem('edupulse_token');
    localStorage.removeItem('edupulse_session');
  },

  getMe: async () => {
    try {
      const res = await fetch(`${getApiUrl()}/auth/me`, { headers: getHeaders() });
      return res.ok ? await res.json() : null;
    } catch (e) {
      return null;
    }
  },

  // ── Faculty endpoints ──────────────────────────────────────────────────────
  getAllFaculties: async (college, dept) => {
    try {
      let url = `${getApiUrl()}/faculty/list`;
      const params = new URLSearchParams();
      if (college) params.append('college', college);
      if (dept) params.append('dept', dept);
      if (params.toString()) url += `?${params.toString()}`;

      const res = await fetch(url, { headers: getHeaders() });
      if (!res.ok) {
        console.error('getAllFaculties failed:', res.status);
        return [];
      }
      const list = await res.json();
      return list.map(f => {
        const dimObj = f.dimension_scores || {};
        const scores = {
          clarity: dimObj.clarity ?? 3.8,
          punctuality: dimObj.punctuality ?? 4.0,
          fairness: dimObj.fairness ?? 3.5,
          approachability: dimObj.approachability ?? 4.1,
          methodology: dimObj.methodology ?? 3.6,
          pacing: dimObj.pacing ?? 3.7,
          ...dimObj
        };
        const trendList = (f.score_trend && f.score_trend.length > 0)
          ? f.score_trend.map(t => t.composite_score)
          : [3.4, 3.6, 3.7, 3.8];

        return {
          id: f.id,
          user_id: f.user_id || f.id,
          name: f.name,
          code: f.faculty_code || f.code,
          dept: f.dept,
          subject: f.subject || 'General',
          college: f.college || 'GEC Thrissur',
          responses: f.response_count ?? f.responses ?? 0,
          composite: f.composite_score ?? 3.5,
          band: f.score_band || (f.composite_score >= 4.0 ? 'strong' : f.composite_score >= 3.0 ? 'developing' : 'needs'),
          scores,
          trend: trendList
        };
      });
    } catch (e) {
      console.error('getAllFaculties error:', e);
      return [];
    }
  },

  getFacultiesByCollege: async (college) => {
    return await DB.getAllFaculties(college);
  },

  getFacultiesByDept: async (dept, college) => {
    return await DB.getAllFaculties(college, dept);
  },

  getEnrolledFaculties: async () => {
    const all = await DB.getAllFaculties();
    try {
      const sessionStr = localStorage.getItem('edupulse_session');
      if (sessionStr) {
        const user = JSON.parse(sessionStr);
        if (user && user.enrolled_faculty_ids) {
          const ids = typeof user.enrolled_faculty_ids === 'string'
            ? JSON.parse(user.enrolled_faculty_ids)
            : user.enrolled_faculty_ids;
          if (Array.isArray(ids) && ids.length > 0) {
            const filtered = all.filter(f => ids.includes(f.id) || ids.includes(f.user_id));
            if (filtered.length > 0) return filtered;
          }
        }
      }
    } catch (e) {
      console.error('Error parsing enrolled faculties:', e);
    }
    return all;
  },

  getFacultyById: async (id) => {
    try {
      const res = await fetch(`${getApiUrl()}/faculty/${encodeURIComponent(id)}`, { headers: getHeaders() });
      return res.ok ? await res.json() : null;
    } catch (e) {
      return null;
    }
  },

  getMyFacultyDashboard: async (term = '2025-S2') => {
    try {
      const res = await fetch(`${getApiUrl()}/faculty/me?term=${encodeURIComponent(term)}`, { headers: getHeaders() });
      return res.ok ? await res.json() : null;
    } catch (e) {
      return null;
    }
  },

  // ── Feedback endpoints ─────────────────────────────────────────────────────
  hasSubmitted: async (facultyProfileId, term = '2025-S2') => {
    try {
      const res = await fetch(
        `${getApiUrl()}/feedback/status?faculty_profile_id=${encodeURIComponent(facultyProfileId)}&term=${encodeURIComponent(term)}`,
        { headers: getHeaders() }
      );
      if (res.ok) {
        const data = await res.json();
        return data.submitted;
      }
      return false;
    } catch (e) {
      return false;
    }
  },

  submitFeedback: async (facultyProfileId, scores, comment = '', term = '2025-S2') => {
    const res = await fetch(`${getApiUrl()}/feedback/submit`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        faculty_profile_id: facultyProfileId,
        term,
        scores,
        comment
      })
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.error || errorData.detail || 'Failed to submit feedback');
    }
    return true;
  },

  // ── Analytics endpoints ────────────────────────────────────────────────────
  getDepartmentAnalytics: async (college, dept) => {
    try {
      let url = `${getApiUrl()}/analytics/departments`;
      const params = new URLSearchParams();
      if (college) params.append('college', college);
      if (dept) params.append('dept', dept);
      if (params.toString()) url += `?${params.toString()}`;

      const res = await fetch(url, { headers: getHeaders() });
      return res.ok ? await res.json() : [];
    } catch (e) {
      return [];
    }
  },

  getFacultyClusters: async (college, k = 3) => {
    try {
      const res = await fetch(
        `${getApiUrl()}/analytics/clusters?college=${encodeURIComponent(college)}&k=${k}`,
        { headers: getHeaders() }
      );
      return res.ok ? await res.json() : [];
    } catch (e) {
      return [];
    }
  },

  getSystemHealth: async (university) => {
    try {
      let url = `${getApiUrl()}/analytics/health`;
      if (university) url += `?university=${encodeURIComponent(university)}`;
      const res = await fetch(url, { headers: getHeaders() });
      return res.ok ? await res.json() : null;
    } catch (e) {
      return null;
    }
  },

  // ── AI Recommendations & Roadmaps ──────────────────────────────────────────
  generateRecommendations: async (facultyProfileId, term = '2025-S2') => {
    const res = await fetch(
      `${getApiUrl()}/recommendations/generate/${encodeURIComponent(facultyProfileId)}?term=${encodeURIComponent(term)}`,
      { method: 'POST', headers: getHeaders() }
    );
    if (!res.ok) throw new Error('Failed to generate recommendations');
    return await res.json();
  },

  getRecommendations: async (facultyProfileId, term = '2025-S2') => {
    try {
      const res = await fetch(
        `${getApiUrl()}/recommendations/${encodeURIComponent(facultyProfileId)}?term=${encodeURIComponent(term)}`,
        { headers: getHeaders() }
      );
      return res.ok ? await res.json() : [];
    } catch (e) {
      return [];
    }
  },

  generateRoadmap: async (facultyProfileId, term = '2025-S2') => {
    const res = await fetch(
      `${getApiUrl()}/recommendations/roadmap/generate/${encodeURIComponent(facultyProfileId)}?term=${encodeURIComponent(term)}`,
      { method: 'POST', headers: getHeaders() }
    );
    if (!res.ok) throw new Error('Failed to generate roadmap');
    return await res.json();
  },

  getRoadmap: async (facultyProfileId, term = '2025-S2') => {
    try {
      const res = await fetch(
        `${getApiUrl()}/recommendations/roadmap/${encodeURIComponent(facultyProfileId)}?term=${encodeURIComponent(term)}`,
        { headers: getHeaders() }
      );
      return res.ok ? await res.json() : null;
    } catch (e) {
      return null;
    }
  },

  // ── Transparency & Methodology ─────────────────────────────────────────────
  getMethodology: async () => {
    try {
      const res = await fetch(`${getApiUrl()}/analytics/methodology`);
      return res.ok ? await res.json() : null;
    } catch (e) {
      console.error('getMethodology error:', e);
      return null;
    }
  },

  getMyStrengthsWeaknesses: async (term = '2025-S2') => {
    try {
      const res = await fetch(
        `${getApiUrl()}/analytics/me/strengths-weaknesses?term=${encodeURIComponent(term)}`,
        { headers: getHeaders() }
      );
      return res.ok ? await res.json() : null;
    } catch (e) {
      console.error('getMyStrengthsWeaknesses error:', e);
      return null;
    }
  },

  // ── Certificate Uploads & Course Completions ──────────────────────────────
  uploadCertificate: async ({ courseKey, courseName, provider, dimensionId, file }) => {
    const formData = new FormData();
    formData.append('course_key', courseKey);
    formData.append('course_name', courseName);
    formData.append('provider', provider);
    formData.append('dimension_id', dimensionId);
    formData.append('certificate', file);

    const token = localStorage.getItem('edupulse_token');
    const headers = token ? { Authorization: `Bearer ${token}` } : {};

    const res = await fetch(`${getApiUrl()}/faculty/courses/complete`, {
      method: 'POST',
      headers,        // NOTE: do NOT set Content-Type — browser sets multipart boundary
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Upload failed');
    }
    return await res.json();
  },

  getCompletedCourses: async () => {
    try {
      const res = await fetch(`${getApiUrl()}/faculty/courses/completed`, {
        headers: getHeaders(),
      });
      return res.ok ? await res.json() : { completions: [], total_boost: 0, completed_count: 0 };
    } catch (e) {
      console.error('getCompletedCourses error:', e);
      return { completions: [], total_boost: 0, completed_count: 0 };
    }
  },

  deleteCourseCompletion: async (completionId) => {
    const res = await fetch(`${getApiUrl()}/faculty/courses/${encodeURIComponent(completionId)}`, {
      method: 'DELETE',
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error('Delete failed');
    return await res.json();
  },
};

