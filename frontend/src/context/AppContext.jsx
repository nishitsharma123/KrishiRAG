import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';

const AppContext = createContext(null);

export const AppProvider = ({ children }) => {
  const [health, setHealth] = useState(null);
  const [loadingHealth, setLoadingHealth] = useState(true);
  const [healthError, setHealthError] = useState(null);

  const [llmStatus, setLlmStatus] = useState(null);
  const [loadingLLM, setLoadingLLM] = useState(true);

  const refreshHealth = useCallback(async () => {
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
  }, []);

  const refreshLLMStatus = useCallback(async () => {
    setLoadingLLM(true);
    try {
      const data = await apiService.getLLMStatus();
      setLlmStatus(data);
    } catch (err) {
      setLlmStatus({
        ollama_available: false,
        model_installed: false,
        system_ready: false,
        error: err.message,
      });
    } finally {
      setLoadingLLM(false);
    }
  }, []);

  const refreshAll = useCallback(() => {
    refreshHealth();
    refreshLLMStatus();
  }, [refreshHealth, refreshLLMStatus]);

  useEffect(() => {
    refreshAll();
    const interval = setInterval(refreshAll, 30000);
    return () => clearInterval(interval);
  }, [refreshAll]);

  return (
    <AppContext.Provider
      value={{
        health,
        loadingHealth,
        healthError,
        refreshHealth,
        llmStatus,
        loadingLLM,
        refreshLLMStatus,
        refreshAll,
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
