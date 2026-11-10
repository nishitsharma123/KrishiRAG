import axios from 'axios';

// Vite proxy forwards /api to backend http://127.0.0.1:8000/api
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Response interceptor for consistent error handling
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
  /**
   * Health diagnostic check
   */
  getHealth: async () => {
    return apiClient.get('/health');
  },

  /**
   * Fetch all registered documents
   */
  getDocuments: async () => {
    return apiClient.get('/documents');
  },
};

export default apiClient;
