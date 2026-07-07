/*
Concept: Login Page
Why it's needed: Authenticates users so they can access the platform.
How it works: Captures username/email and password in state, calls the login function from AuthContext.
Users can toggle between username and email login methods.
*/
import { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import '../styles/Login.css';

const Login = () => {
    const [loginMethod, setLoginMethod] = useState('username'); // 'username' or 'email'
    const [credential, setCredential] = useState(''); // Username or Email
    const [password, setPassword] = useState('');
    const [errors, setErrors] = useState({});
    const [loading, setLoading] = useState(false);
    const { login } = useContext(AuthContext);
    const navigate = useNavigate();

    const validateForm = () => {
        const newErrors = {};

        if (!credential.trim()) {
            newErrors.credential = loginMethod === 'email' 
                ? 'Email is required' 
                : 'Username is required';
        } else if (loginMethod === 'email') {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(credential)) {
                newErrors.credential = 'Please enter a valid email address';
            }
        }

        if (!password) {
            newErrors.password = 'Password is required';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!validateForm()) {
            return;
        }

        setLoading(true);
        const success = await login(credential, password);
        setLoading(false);
        
        if (success) {
            navigate('/dashboard');
        }
    };

    const handleMethodChange = (method) => {
        setLoginMethod(method);
        setCredential('');
        setPassword('');
        setErrors({});
    };

    return (
        <div className="login-container">
            <div className="login-box">
                <div className="login-header">
                    <h2>Login</h2>
                    <p className="login-subtitle">CIS Compliance Audit Platform</p>
                </div>

                <div className="login-method-toggle mb-4">
                    <button
                        type="button"
                        className={`toggle-btn ${loginMethod === 'username' ? 'active' : ''}`}
                        onClick={() => handleMethodChange('username')}
                    >
                        <i className="icon">👤</i> Username
                    </button>
                    <button
                        type="button"
                        className={`toggle-btn ${loginMethod === 'email' ? 'active' : ''}`}
                        onClick={() => handleMethodChange('email')}
                    >
                        <i className="icon">✉️</i> Email
                    </button>
                </div>

                <form onSubmit={handleSubmit}>
                    <div className="mb-3">
                        <label className="form-label">
                            {loginMethod === 'email' ? 'Email Address' : 'Username'}
                        </label>
                        <input 
                            type={loginMethod === 'email' ? 'email' : 'text'}
                            className={`form-control ${errors.credential ? 'is-invalid' : ''}`}
                            value={credential} 
                            onChange={(e) => {
                                setCredential(e.target.value);
                                if (errors.credential) setErrors({...errors, credential: ''});
                            }}
                            placeholder={loginMethod === 'email' ? 'your@email.com' : 'username'}
                            required 
                        />
                        {errors.credential && (
                            <div className="invalid-feedback d-block">
                                {errors.credential}
                            </div>
                        )}
                    </div>

                    <div className="mb-4">
                        <label className="form-label">Password</label>
                        <input 
                            type="password" 
                            className={`form-control ${errors.password ? 'is-invalid' : ''}`}
                            value={password} 
                            onChange={(e) => {
                                setPassword(e.target.value);
                                if (errors.password) setErrors({...errors, password: ''});
                            }}
                            placeholder="Enter your password"
                            required 
                        />
                        {errors.password && (
                            <div className="invalid-feedback d-block">
                                {errors.password}
                            </div>
                        )}
                    </div>

                    <button 
                        type="submit" 
                        className="btn btn-primary btn-login w-100"
                        disabled={loading}
                    >
                        {loading ? (
                            <>
                                <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                                Logging in...
                            </>
                        ) : (
                            'Login'
                        )}
                    </button>
                </form>

                <div className="login-footer">
                    <p className="text-center mt-4">
                        Don't have an account? <Link to="/register" className="register-link">Register here</Link>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Login;
