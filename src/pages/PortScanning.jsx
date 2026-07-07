/*
Concept: Port Scanning Page
Why it's needed: Allows users to scan open ports on registered systems for security assessment.
How it works: Displays systems and allows port scanning with results showing open services.
*/
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';
import { toast } from 'react-toastify';
import '../styles/PortScanning.css';

const PortScanning = () => {
    const [systems, setSystems] = useState([]);
    const [selectedSystem, setSelectedSystem] = useState('');
    const [customPorts, setCustomPorts] = useState('');
    const [scanning, setScanning] = useState(false);
    const [scanResults, setScanResults] = useState(null);
    const [errors, setErrors] = useState({});
    const navigate = useNavigate();

    useEffect(() => {
        fetchSystems();
    }, []);

    const fetchSystems = async () => {
        try {
            const res = await api.get('/audits/systems');
            setSystems(res.data);
            if (res.data.length > 0) setSelectedSystem(res.data[0].id);
        } catch (error) {
            toast.error('Failed to fetch systems');
        }
    };

    const validatePorts = (portString) => {
        if (!portString.trim()) return null; // Use default ports
        
        try {
            const ports = portString
                .split(',')
                .map(p => {
                    const port = parseInt(p.trim());
                    if (isNaN(port) || port < 1 || port > 65535) {
                        throw new Error(`Invalid port: ${p.trim()}`);
                    }
                    return port;
                });
            
            if (ports.length > 100) {
                throw new Error('Cannot scan more than 100 ports');
            }
            
            return ports;
        } catch (err) {
            setErrors({ customPorts: err.message });
            return false;
        }
    };

    const handleScanCommonPorts = async () => {
        if (!selectedSystem) {
            toast.warning('Please select a system first');
            return;
        }

        setScanning(true);
        setScanResults(null);
        setErrors({});

        try {
            toast.info('Scanning common ports... This may take a moment.');
            const res = await api.post(`/audits/scan-ports/${selectedSystem}`);
            setScanResults(res.data);
            toast.success(`Port scan completed! Found ${res.data.scan_summary.open_ports} open ports.`);
        } catch (error) {
            const errorMessage = error.response?.data?.detail || 'Port scan failed';
            setErrors({ scan: errorMessage });
            toast.error(errorMessage);
        } finally {
            setScanning(false);
        }
    };

    const handleScanCustomPorts = async () => {
        if (!selectedSystem) {
            toast.warning('Please select a system first');
            return;
        }

        const ports = validatePorts(customPorts);
        if (ports === false) return; // Validation error

        setScanning(true);
        setScanResults(null);
        setErrors({});

        try {
            const endpoint = ports ? `/audits/scan-ports/${selectedSystem}` : `/audits/scan-ports/${selectedSystem}/common`;
            const config = ports ? { params: { custom_ports: ports.join(',') } } : {};
            
            toast.info('Scanning ports... This may take a moment.');
            const res = ports ? await api.post(endpoint, null, config) : await api.get(endpoint);
            setScanResults(res.data);
            toast.success(`Port scan completed! Found ${res.data.open_ports_count || res.data.scan_summary.open_ports} open ports.`);
        } catch (error) {
            const errorMessage = error.response?.data?.detail || 'Port scan failed';
            setErrors({ scan: errorMessage });
            toast.error(errorMessage);
        } finally {
            setScanning(false);
        }
    };

    return (
        <div>
            <Navbar />
            <div className="d-flex">
                <Sidebar />
                <div className="flex-grow-1 p-4">
                    <h2>Port Scanning</h2>
                    <p className="text-muted">Scan open ports on your registered systems to identify active services.</p>

                    <div className="row mt-4">
                        <div className="col-md-4">
                            <div className="card p-4 mb-4">
                                <h4>Select System</h4>
                                <div className="form-group">
                                    <label>Target System</label>
                                    <select 
                                        className="form-select" 
                                        value={selectedSystem}
                                        onChange={(e) => {
                                            setSelectedSystem(e.target.value);
                                            setScanResults(null);
                                        }}
                                    >
                                        <option value="">Choose a system...</option>
                                        {systems.map(sys => (
                                            <option key={sys.id} value={sys.id}>
                                                {sys.hostname} ({sys.ip_address})
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                <hr />

                                <h5>Quick Scan</h5>
                                <p className="small text-muted">
                                    Scans 20 common service ports (HTTP, SSH, DNS, etc.)
                                </p>
                                <button 
                                    className="btn btn-primary w-100 mb-3"
                                    onClick={handleScanCommonPorts}
                                    disabled={scanning || !selectedSystem}
                                >
                                    {scanning ? 'Scanning...' : 'Scan Common Ports'}
                                </button>

                                <hr />

                                <h5>Custom Ports</h5>
                                <div className="form-group">
                                    <label className="small">Port Numbers (comma-separated)</label>
                                    <textarea 
                                        className={`form-control ${errors.customPorts ? 'is-invalid' : ''}`}
                                        rows="3"
                                        placeholder="e.g., 22, 80, 443, 3306, 5432"
                                        value={customPorts}
                                        onChange={(e) => {
                                            setCustomPorts(e.target.value);
                                            if (errors.customPorts) setErrors({});
                                        }}
                                        disabled={scanning}
                                    />
                                    {errors.customPorts && (
                                        <div className="invalid-feedback d-block">
                                            {errors.customPorts}
                                        </div>
                                    )}
                                    <small className="form-text text-muted d-block mt-2">
                                        Max 100 ports. Leave empty to scan common ports.
                                    </small>
                                </div>

                                <button 
                                    className="btn btn-outline-primary w-100"
                                    onClick={handleScanCustomPorts}
                                    disabled={scanning || !selectedSystem}
                                >
                                    {scanning ? 'Scanning...' : 'Scan Custom Ports'}
                                </button>
                            </div>
                        </div>

                        <div className="col-md-8">
                            <div className="card p-4">
                                <h4>Scan Results</h4>
                                
                                {errors.scan && (
                                    <div className="alert alert-danger" role="alert">
                                        {errors.scan}
                                    </div>
                                )}

                                {!scanResults && !scanning && (
                                    <div className="alert alert-info">
                                        Select a system and click "Scan" to start port scanning.
                                    </div>
                                )}

                                {scanning && (
                                    <div className="text-center py-5">
                                        <div className="spinner-border text-primary mb-3" role="status">
                                            <span className="visually-hidden">Scanning...</span>
                                        </div>
                                        <p>Scanning ports on the system... This may take a moment.</p>
                                    </div>
                                )}

                                {scanResults && (
                                    <div className="scan-results">
                                        <div className="system-info mb-4 p-3 bg-light rounded">
                                            <strong>System:</strong> {scanResults.hostname} ({scanResults.ip_address}) <br />
                                            <strong>Total Scanned:</strong> {scanResults.scan_summary?.total_scanned || scanResults.total_scanned} ports
                                        </div>

                                        <div className="scan-summary mb-4">
                                            <div className="row">
                                                <div className="col-md-4">
                                                    <div className="summary-box open">
                                                        <h3>{scanResults.scan_summary?.open_ports || scanResults.open_ports_count || 0}</h3>
                                                        <p>Open Ports</p>
                                                    </div>
                                                </div>
                                                <div className="col-md-4">
                                                    <div className="summary-box closed">
                                                        <h3>{scanResults.scan_summary?.closed_ports || 0}</h3>
                                                        <p>Closed Ports</p>
                                                    </div>
                                                </div>
                                                <div className="col-md-4">
                                                    <div className="summary-box error">
                                                        <h3>{scanResults.scan_summary?.errors || 0}</h3>
                                                        <p>Errors</p>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        {(scanResults.open_services || scanResults.open_ports_count > 0) && (
                                            <div className="open-services mb-4">
                                                <h5>Open Services</h5>
                                                <div className="table-responsive">
                                                    <table className="table table-sm table-hover">
                                                        <thead className="table-light">
                                                            <tr>
                                                                <th>Port</th>
                                                                <th>Service</th>
                                                                <th>Status</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            {(scanResults.open_services || []).map((port, idx) => (
                                                                <tr key={idx} className="service-open">
                                                                    <td><strong>{port.port}</strong></td>
                                                                    <td>{port.service}</td>
                                                                    <td>
                                                                        <span className="badge bg-success">
                                                                            {port.status}
                                                                        </span>
                                                                    </td>
                                                                </tr>
                                                            ))}
                                                        </tbody>
                                                    </table>
                                                </div>
                                            </div>
                                        )}

                                        <details className="all-results">
                                            <summary className="cursor-pointer">View All Results ({(scanResults.all_results || scanResults.results || []).length} ports)</summary>
                                            <div className="table-responsive mt-3">
                                                <table className="table table-sm">
                                                    <thead className="table-light">
                                                        <tr>
                                                            <th>Port</th>
                                                            <th>Service</th>
                                                            <th>Status</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {(scanResults.all_results || scanResults.results || []).map((port, idx) => (
                                                            <tr key={idx} className={`status-${port.status}`}>
                                                                <td>{port.port}</td>
                                                                <td>{port.service}</td>
                                                                <td>
                                                                    <span className={`badge bg-${port.status === 'open' ? 'success' : port.status === 'closed' ? 'secondary' : 'warning'}`}>
                                                                        {port.status}
                                                                    </span>
                                                                    {port.error && <small className="text-danger ms-2">{port.error}</small>}
                                                                </td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            </div>
                                        </details>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PortScanning;
