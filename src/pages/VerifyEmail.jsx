/*
Concept: Email Verification Page
Why it's needed: After registration, users need to verify their email by entering the OTP code sent to their email.
How it works: Takes OTP code, calls the verify-otp endpoint to mark email as verified.
*/
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { toast } from 'react-toastify';
import '../styles/VerifyEmail.css';

const VerifyEmail = () => {
    const [otp, setOtp] = useState('');
    const [resending, setResending] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleVerify = async (e) => {
        e.preventDefault();
        
        if (!otp || otp.length !== 6 || !otp.isDigit?.()) {
            setError('Please enter a valid 6-digit code');
            return;
        }

        setLoading(true);
        setError('');

        try {
            const response = await api.post('/api/auth/verify-otp', {
                otp_code: otp
            });
            
            toast.success('Email verified successfully!');
            navigate('/dashboard');
        } catch (err) {
            const errorMessage = err.response?.data?.detail || 'Invalid or expired OTP code';
            setError(errorMessage);
            toast.error(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    const handleResendOTP = async () => {
        setResending(true);
        setError('');

        try {
            // Get email from localStorage or auth context
            const userEmail = localStorage.getItem('userEmail');
            
            if (!userEmail) {
                setError('Email not found. Please register again.');
                return;
            }

            await api.post('/api/auth/resend-otp', {
                email: userEmail
            });
            
            toast.success('A new verification code has been sent to your email!');
        } catch (err) {
            const errorMessage = err.response?.data?.detail || 'Failed to resend OTP';
            setError(errorMessage);
            toast.error(errorMessage);
        } finally {
            setResending(false);
        }
    };

    return (
        <div className="verify-email-container">
            <div className="verify-email-box">
                <h2>Verify Your Email</h2>
                <p className="verify-description">
                    We've sent a 6-digit verification code to your email address.
                    Enter it below to verify your account.
                </p>

                {error && (
                    <div className="alert alert-danger" role="alert">
                        {error}
                    </div>
                )}

                <form onSubmit={handleVerify}>
                    <div className="form-group">
                        <label htmlFor="otp">Verification Code</label>
                        <input
                            id="otp"
                            type="text"
                            inputMode="numeric"
                            maxLength="6"
                            className={`form-control otp-input ${error ? 'is-invalid' : ''}`}
                            value={otp}
                            onChange={(e) => {
                                const value = e.target.value.replace(/[^0-9]/g, '');
                                setOtp(value);
                                if (error) setError('');
                            }}
                            placeholder="000000"
                            required
                        />
                        <small className="form-text text-muted">
                            Enter the 6-digit code from your email
                        </small>
                    </div>

                    <button
                        type="submit"
                        className="btn btn-primary btn-block"
                        disabled={loading || otp.length !== 6}
                    >
                        {loading ? 'Verifying...' : 'Verify Email'}
                    </button>
                </form>

                <div className="resend-section">
                    <p>Didn't receive the code?</p>
                    <button
                        type="button"
                        className="btn btn-link"
                        onClick={handleResendOTP}
                        disabled={resending}
                    >
                        {resending ? 'Sending...' : 'Resend Code'}
                    </button>
                </div>

                <div className="help-text">
                    <small>
                        The verification code expires in 10 minutes.
                    </small>
                </div>
            </div>
        </div>
    );
};

export default VerifyEmail;
