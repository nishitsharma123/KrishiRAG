import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiService } from '../services/api';

const AppContext = createContext(null);

export const AppProvider = ({ children }) => {
  const [health, setHealth] = useState(null);
  const [loadingHealth, setLoadingHealth] = useState(true);
  const [healthError, setHealthError] = useState(null);

  const refreshHealth = async () => {
    setLoadingHealth(true);
    setHealthError(null);
    try {
      const data = await apiService.getHealth();
      setHealth(data);
    } catch (err) {
      setHealthError(err.message || 'Failed to connect to KrishiRAG backend');
    } finally {
      setLoadingHealth(false);
    }
  };

  useEffect(() => {
    refreshHealth();
    // Periodically poll health every 30 seconds
    const interval = setInterval(refreshHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <AppContext.Provider
      value={{
        health,
        loadingHealth,
        healthError,
        refreshHealth,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
