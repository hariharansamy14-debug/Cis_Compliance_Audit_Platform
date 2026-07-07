/*
Concept: Navigation Bar Component
Why it's needed: Provides a consistent header across pages, showing the user's status and a logout button.
*/
import { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const Navbar = () => {
    const { user, logout } = useContext(AuthContext);
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
            <div className="container-fluid">
                <span className="navbar-brand mb-0 h1">CIS Compliance Platform</span>
                <div className="d-flex text-white align-items-center">
                    {user && (
                        <>
                            <span className="me-3">Welcome, {user.username}</span>
                            <button className="btn btn-outline-light btn-sm" onClick={handleLogout}>Logout</button>
                        </>
                    )}
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
