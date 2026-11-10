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
      message: error.response?.data?.error?.message || error.message || 'An unexpected error occurred',
      code: error.response?.data?.error?.code || 'NETWORK_ERROR',
      status: error.response?.status,
    };
    return Promise.reject(errorPayload);
  }
);

export const apiService = {
  getHealth: async () => {
    return apiClient.get('/health');
  },

  getDocuments: async () => {
    return apiClient.get('/documents');
  },

  getDocument: async (documentId) => {
    return apiClient.get(`/documents/${documentId}`);
  },

  getDocumentChunks: async (documentId, params = {}) => {
    return apiClient.get(`/documents/${documentId}/chunks`, { params });
  },

  uploadDocument: async (formData) => {
    return apiClient.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 120000,
    });
  },

  searchRetrieval: async (data) => {
    return apiClient.post('/retrieval/search', data);
  },

  getIndexingStatus: async () => {
    return apiClient.get('/retrieval/index/status');
  },

  triggerIndexing: async (params = {}) => {
    return apiClient.post('/retrieval/index', null, { 
      params,
      timeout: 600000, // 10 minutes for full reindexing
    });
  },

  askChat: async (data) => {
    return apiClient.post('/chat', data, {
      timeout: 240000, // 4 minutes to allow local CPU LLM inference
    });
  },

  getChatHistory: async (sessionId) => {
    return apiClient.get(`/chat/history/${sessionId}`);
  },

  getLLMStatus: async () => {
    return apiClient.get('/chat/status');
  },
};

export default apiClient;
