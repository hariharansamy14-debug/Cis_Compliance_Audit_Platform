/*
Concept: Dashboard Page
Why it's needed: Provides a high-level overview of the user's systems and recent audit compliance scores.
How it works: Fetches systems and audit history from the API and displays them in Bootstrap cards.
*/
import { useEffect, useState } from 'react';
import api from '../services/api';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';
import { toast } from 'react-toastify';

const Dashboard = () => {
    const [systems, setSystems] = useState([]);
    const [recentAudits, setRecentAudits] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDashboardData = async () => {
            try {
                const sysRes = await api.get('/audits/systems');
                setSystems(sysRes.data);

                const auditRes = await api.get('/audits/history');
                setRecentAudits(auditRes.data.slice(0, 5)); // Get top 5 recent
            } catch (error) {
                toast.error("Failed to load dashboard data");
            } finally {
                setLoading(false);
            }
        };
        fetchDashboardData();
    }, []);

    if (loading) return <div>Loading dashboard...</div>;

    return (
        <div>
            <Navbar />
            <div className="d-flex">
                <Sidebar />
                <div className="flex-grow-1 p-4">
                    <h2>Dashboard</h2>
                    <div className="row mt-4">
                        <div className="col-md-4">
                            <div className="card bg-primary text-white text-center p-3">
                                <h4>Total Systems</h4>
                                <h2>{systems.length}</h2>
                            </div>
                        </div>
                        <div className="col-md-4">
                            <div className="card bg-success text-white text-center p-3">
                                <h4>Total Audits Run</h4>
                                <h2>{recentAudits.length} (Recent)</h2>
                            </div>
                        </div>
                    </div>

                    <h4 className="mt-5">Recent Audits</h4>
                    {recentAudits.length > 0 ? (
                        <table className="table table-hover mt-3">
                            <thead className="table-dark">
                                <tr>
                                    <th>Date</th>
                                    <th>Score</th>
                                    <th>Passed</th>
                                    <th>Failed</th>
                                </tr>
                            </thead>
                            <tbody>
                                {recentAudits.map(audit => (
                                    <tr key={audit.id}>
                                        <td>{new Date(audit.audit_date).toLocaleString()}</td>
                                        <td>
                                            <span className={`badge ${audit.compliance_score > 80 ? 'bg-success' : audit.compliance_score > 50 ? 'bg-warning' : 'bg-danger'}`}>
                                                {audit.compliance_score}%
                                            </span>
                                        </td>
                                        <td>{audit.passed_checks}</td>
                                        <td>{audit.failed_checks}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    ) : (
                        <p className="mt-3 text-muted">No audits have been run yet.</p>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
