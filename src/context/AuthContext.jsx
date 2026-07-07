import { createContext, useState, useEffect } from 'react';
import api from '../services/api';
import { toast } from 'react-toastify';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const fetchMe = async () => {
        try {
            const res = await api.get('/auth/me');
            setUser(res.data);
            return res.data;
        } catch (error) {
            console.error("Failed to load user profile:", error);
            logout();
        }
    };

    useEffect(() => {
        const initAuth = async () => {
            const token = localStorage.getItem('token');
            if (token) {
                await fetchMe();
            }
            setLoading(false);
        };
        initAuth();
    }, []);

    const login = async (username, password) => {
        try {
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);
            
            const response = await api.post('/auth/login', formData, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            });
            
            localStorage.setItem('token', response.data.access_token);
            localStorage.setItem('refreshToken', response.data.refresh_token);
            
            setUser(response.data.user);
            toast.success("Welcome back!");
            return true;
        } catch (error) {
            toast.error(error.response?.data?.detail || "Login failed");
            return false;
        }
    };

    const register = async (userData) => {
        try {
            const res = await api.post('/auth/register', userData);
            toast.success(res.data.message || "Registration successful! Verification code sent.");
            return res.data.user;
        } catch (error) {
            toast.error(error.response?.data?.detail || "Registration failed");
            return null;
        }
    };

    const verifyOtp = async (otpCode) => {
        try {
            const res = await api.post('/auth/verify-otp', { otp_code: otpCode });
            setUser(res.data.user);
            toast.success("Email verified successfully!");
            return true;
        } catch (error) {
            toast.error(error.response?.data?.detail || "Verification failed");
            return false;
        }
    };

    const resendOtp = async (email) => {
        try {
            const res = await api.post('/auth/resend-otp', { email });
            toast.success(res.data.message || "Verification code resent.");
            return true;
        } catch (error) {
            toast.error(error.response?.data?.detail || "Failed to resend code");
            return false;
        }
    };

    const logout = async () => {
        try {
            await api.post('/auth/logout');
        } catch (e) {
            // Ignore if unauthorized
        }
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
        setUser(null);
        toast.info("Logged out successfully");
    };

    // RBAC helpers
    const hasRole = (allowedRoles) => {
        if (!user) return false;
        const normalized = user.role.toLowerCase().replace(" ", "_");
        return allowedRoles.some(r => r.toLowerCase().replace(" ", "_") === normalized);
    };

    const hasPermission = (permission) => {
        if (!user) return false;
        const role = user.role.toLowerCase().replace(" ", "_");
        
        // Admin overrides all
        if (role === "administrator" || role === "admin") return true;
        
        // Simple client-side permissions matching
        const permissions = {
            security_analyst: [
                "systems.read", "systems.create", "systems.update", "systems.delete",
                "audits.read", "audits.run", "audits.delete",
                "reports.read", "reports.create", "reports.delete",
                "benchmarks.read", "benchmarks.manage",
                "notifications.read", "notifications.manage",
                "dashboard.read", "users.read"
            ],
            auditor: [
                "systems.read", "audits.read", "audits.run",
                "reports.read", "reports.create", "benchmarks.read",
                "notifications.read", "dashboard.read"
            ],
            viewer: [
                "systems.read", "audits.read", "reports.read",
                "benchmarks.read", "notifications.read", "dashboard.read"
            ]
        };
        
        const rolePerms = permissions[role] || [];
        if (rolePerms.includes(permission)) return true;
        
        // Wildcard match systems.*
        const prefix = permission.split(".")[0] + ".*";
        if (rolePerms.includes(prefix)) return true;
        
        return false;
    };

    return (
        <AuthContext.Provider value={{ user, loading, login, register, verifyOtp, resendOtp, logout, hasRole, hasPermission }}>
            {children}
        </AuthContext.Provider>
    );
};
