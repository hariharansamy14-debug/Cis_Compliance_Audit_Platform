/*
Concept: Audit History Page
Why it's needed: Users need to view past audits and download reports.
How it works: Fetches history from API, displays a table, and uses `window.open` to hit the download API endpoints.
*/
import { useEffect, useState } from 'react';
import api from '../services/api';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';
import { toast } from 'react-toastify';

const AuditHistory = () => {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedAudit, setSelectedAudit] = useState(null);

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const res = await api.get('/audits/history');
                setHistory(res.data);
            } catch (error) {
                toast.error("Failed to load history");
            } finally {
                setLoading(false);
            }
        };
        fetchHistory();
    }, []);

    const handleDownload = (auditId, format) => {
        api.get(`/reports/download/${auditId}/${format}`, { responseType: 'blob' })
            .then(response => {
                const url = window.URL.createObjectURL(new Blob([response.data]));
                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', `report_${auditId}.${format}`);
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);
            })
            .catch(() => toast.error("Failed to download report"));
    };

    return (
        <div>
            <Navbar />
            <div className="d-flex">
                <Sidebar />
                <div className="flex-grow-1 p-4">
                    <h2>Audit History & Reports</h2>
                    
                    {loading ? <p>Loading...</p> : (
                        <div className="card mt-4 p-3">
                            <table className="table table-hover">
                                <thead className="table-light">
                                    <tr>
                                        <th>Date</th>
                                        <th>Score</th>
                                        <th>Passed / Failed</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {history.map(audit => (
                                        <tr key={audit.id}>
                                            <td>{new Date(audit.audit_date).toLocaleString()}</td>
                                            <td>
                                                <span className={`badge ${audit.compliance_score > 80 ? 'bg-success' : audit.compliance_score > 50 ? 'bg-warning' : 'bg-danger'}`}>
                                                    {audit.compliance_score}%
                                                </span>
                                            </td>
                                            <td>{audit.passed_checks} / {audit.failed_checks}</td>
                                            <td>
                                                <button className="btn btn-sm btn-info me-2 text-white" onClick={() => setSelectedAudit(audit)}>View Details</button>
                                                <button className="btn btn-sm btn-outline-secondary me-2" onClick={() => handleDownload(audit.id, 'json')}>JSON</button>
                                                <button className="btn btn-sm btn-outline-secondary" onClick={() => handleDownload(audit.id, 'csv')}>CSV</button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {/* Details Modal (Simplified as inline rendering for now) */}
                    {selectedAudit && (
                        <div className="card mt-4 p-4 border-info">
                            <div className="d-flex justify-content-between">
                                <h4>Audit Details</h4>
                                <button className="btn-close" onClick={() => setSelectedAudit(null)}></button>
                            </div>
                            <ul className="list-group mt-3">
                                {selectedAudit.results.map((res, idx) => (
                                    <li key={idx} className="list-group-item d-flex justify-content-between align-items-center">
                                        <div>
                                            <strong>{res.check}</strong> <br/>
                                            <small className="text-muted">{res.details}</small>
                                        </div>
                                        <span className={`badge ${res.status === 'Passed' ? 'bg-success' : 'bg-danger'}`}>
                                            {res.status}
                                        </span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default AuditHistory;
