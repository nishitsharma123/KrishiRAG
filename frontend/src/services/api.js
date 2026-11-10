import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const errorPayload = {
      message: error.response?.data?.detail || error.response?.data?.error?.message || error.message || 'An unexpected error occurred',
      code: error.response?.data?.error?.code || 'NETWORK_ERROR',
      status: error.response?.status,
    };
    return Promise.reject(errorPayload);
  }
);

// 1. Chat API Service
export const chatApi = {
  ask: async (data) => {
    return apiClient.post('/chat', data, {
      timeout: 240000, // 4 minutes for local CPU Ollama inference
    });
  },

  getHistory: async (sessionId) => {
    return apiClient.get(`/chat/history/${sessionId}`);
  },

  getSessions: async () => {
    return apiClient.get('/chat/sessions');
  },

  deleteSession: async (sessionId) => {
    return apiClient.delete(`/chat/sessions/${sessionId}`);
  },

  getStatus: async () => {
    return apiClient.get('/chat/status');
  },
};

// 2. Feedback API Service
export const feedbackApi = {
  submit: async (messageId, rating, comment = null) => {
    return apiClient.post('/chat/feedback', {
      message_id: messageId,
      rating,
      comment,
    });
  },
};

// 3. Document API Service
export const documentApi = {
  getAll: async () => {
    return apiClient.get('/documents');
  },

  getById: async (documentId) => {
    return apiClient.get(`/documents/${documentId}`);
  },

  getChunks: async (documentId, params = {}) => {
    return apiClient.get(`/documents/${documentId}/chunks`, { params });
  },

  upload: async (formData) => {
    return apiClient.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 180000,
    });
  },

  delete: async (documentId) => {
    return apiClient.delete(`/documents/${documentId}`);
  },
};

// 4. Admin API Service
export const adminApi = {
  getStats: async () => {
    return apiClient.get('/admin/stats');
  },
};

// 5. Evaluation API Service
export const evaluationApi = {
  getMetrics: async () => {
    return apiClient.get('/evaluation/metrics');
  },
};

// 6. Retrieval & Indexing API Service
export const retrievalApi = {
  search: async (data) => {
    return apiClient.post('/retrieval/search', data);
  },

  getIndexStatus: async () => {
    return apiClient.get('/retrieval/index/status');
  },

  triggerIndex: async (params = {}) => {
    return apiClient.post('/retrieval/index', null, { 
      params,
      timeout: 600000, 
    });
  },
};

// Legacy unified export for backward compatibility
export const apiService = {
  getHealth: async () => apiClient.get('/health'),
  getDocuments: documentApi.getAll,
  getDocument: documentApi.getById,
  getDocumentChunks: documentApi.getChunks,
  uploadDocument: documentApi.upload,
  deleteDocument: documentApi.delete,
  searchRetrieval: retrievalApi.search,
  getIndexingStatus: retrievalApi.getIndexStatus,
  triggerIndexing: retrievalApi.triggerIndex,
  askChat: chatApi.ask,
  getChatHistory: chatApi.getHistory,
  getChatSessions: chatApi.getSessions,
  deleteChatSession: chatApi.deleteSession,
  getLLMStatus: chatApi.getStatus,
  submitFeedback: feedbackApi.submit,
  getAdminStats: adminApi.getStats,
  getEvaluationMetrics: evaluationApi.getMetrics,
};

export default apiClient;
