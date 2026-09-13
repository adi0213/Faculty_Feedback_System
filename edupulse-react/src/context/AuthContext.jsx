import React, { createContext, useContext, useState, useEffect } from 'react';
import { DB } from '../data/db';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const session = localStorage.getItem('edupulse_session');
    if (session) {
      try {
        setUser(JSON.parse(session));
      } catch (e) {
        localStorage.removeItem('edupulse_session');
      }
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    const session = await DB.login(email, password);
    if (session) {
      setUser(session);
      localStorage.setItem('edupulse_session', JSON.stringify(session));
      return session;
    }
    return null;
  };

  const logout = () => {
    setUser(null);
    DB.logout();
    localStorage.removeItem('edupulse_session');
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
