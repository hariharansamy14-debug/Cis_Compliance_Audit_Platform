import axios from 'axios';

const API_URL = '/api/v1';

const api = axios.create({
    baseURL: API_URL,
});

// Request interceptor: attach access token
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
}, (error) => {
    return Promise.reject(error);
});

// Response interceptor: handle 401 token refresh
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
    failedQueue.forEach(prom => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });
    failedQueue = [];
};

api.interceptors.response.use((response) => {
    return response;
}, async (error) => {
    const originalRequest = error.config;
    
    // Check if error is 401 and request wasn't a refresh call
    if (error.response?.status === 401 && !originalRequest._retry && !originalRequest.url.includes('/auth/login') && !originalRequest.url.includes('/auth/refresh')) {
        
        if (isRefreshing) {
            return new Promise((resolve, reject) => {
                failedQueue.push({ resolve, reject });
            })
            .then(token => {
                originalRequest.headers.Authorization = 'Bearer ' + token;
                return api(originalRequest);
            })
            .catch(err => {
                return Promise.reject(err);
            });
        }

        originalRequest._retry = true;
        isRefreshing = true;

        const refreshToken = localStorage.getItem('refreshToken');
        if (!refreshToken) {
            isRefreshing = false;
            // Clear credentials and force login if no refresh token
            localStorage.removeItem('token');
            window.location.href = '/login';
            return Promise.reject(error);
        }

        try {
            const res = await axios.post(`${API_URL}/auth/refresh`, { refresh_token: refreshToken });
            const newAccessToken = res.data.access_token;
            
            localStorage.setItem('token', newAccessToken);
            api.defaults.headers.common['Authorization'] = 'Bearer ' + newAccessToken;
            originalRequest.headers.Authorization = 'Bearer ' + newAccessToken;
            
            processQueue(null, newAccessToken);
            isRefreshing = false;
            
            return api(originalRequest);
        } catch (refreshError) {
            processQueue(refreshError, null);
            isRefreshing = false;
            
            // Wipe token records and route back
            localStorage.removeItem('token');
            localStorage.removeItem('refreshToken');
            window.location.href = '/login';
            return Promise.reject(refreshError);
        }
    }
    
    return Promise.reject(error);
});

export default api;
