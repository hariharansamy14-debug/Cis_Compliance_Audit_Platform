import { Outlet } from 'react-router-dom';

const AuthLayout = () => {
    return (
        <div style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'radial-gradient(circle at center, #111a2e 0%, #070a13 100%)',
            padding: '2rem'
        }}>
            <div className="card-glass animate-slide-up" style={{
                width: '100%',
                maxWidth: '420px',
                padding: '2.5rem',
                boxShadow: 'var(--shadow-lg)'
            }}>
                <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
                    <div style={{
                        fontSize: '3rem',
                        marginBottom: '0.5rem',
                        background: 'linear-gradient(135deg, var(--primary), var(--secondary))',
                        webkitBackgroundClip: 'text',
                        webkitTextFillColor: 'transparent',
                        fontWeight: 'bold',
                        display: 'inline-block'
                    }}>
                        🛡️
                    </div>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: 700, letterSpacing: '-0.025em' }}>
                        CIS Compliance
                    </h2>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginTop: '0.25rem' }}>
                        Enterprise Security Audit Platform
                    </p>
                </div>
                <Outlet />
            </div>
        </div>
    );
};

export default AuthLayout;
