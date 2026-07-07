/*
Concept: Sidebar Navigation
Why it's needed: Allows users to navigate between different features of the application (Dashboard, Run Audit, History, Port Scanning).
*/
import { Link, useLocation } from 'react-router-dom';

const Sidebar = () => {
    const location = useLocation();

    return (
        <div className="bg-white sidebar p-3" style={{ width: '250px' }}>
            <h5 className="mb-4 text-primary">Menu</h5>
            <ul className="nav flex-column gap-2">
                <li className="nav-item">
                    <Link to="/dashboard" className={`nav-link rounded ${location.pathname === '/dashboard' ? 'bg-primary text-white' : 'text-dark'}`}>
                        Dashboard
                    </Link>
                </li>
                <li className="nav-item">
                    <Link to="/run-audit" className={`nav-link rounded ${location.pathname === '/run-audit' ? 'bg-primary text-white' : 'text-dark'}`}>
                        Run Audit
                    </Link>
                </li>
                <li className="nav-item">
                    <Link to="/port-scanning" className={`nav-link rounded ${location.pathname === '/port-scanning' ? 'bg-primary text-white' : 'text-dark'}`}>
                        Port Scanning
                    </Link>
                </li>
                <li className="nav-item">
                    <Link to="/history" className={`nav-link rounded ${location.pathname === '/history' ? 'bg-primary text-white' : 'text-dark'}`}>
                        Audit History
                    </Link>
                </li>
            </ul>
        </div>
    );
};

export default Sidebar;
