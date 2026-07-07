/*
Concept: Run Audit Page
Why it's needed: Allows users to add a new system and trigger an audit script on it.
How it works: A form to add a system with IP and OS validation, and a button to trigger the API endpoint that runs the audit script.
*/
import { useState, useEffect } from 'react';
import api from '../services/api';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';
import { toast } from 'react-toastify';
import { useNavigate } from 'react-router-dom';

const RunAudit = () => {
    const [systems, setSystems] = useState([]);
    const [newSystem, setNewSystem] = useState({ hostname: '', operating_system: 'windows', ip_address: '' });
    const [selectedSystem, setSelectedSystem] = useState('');
    const [isAuditing, setIsAuditing] = useState(false);
    const [errors, setErrors] = useState({});
    const navigate = useNavigate();
    const backendBaseUrl = api.defaults.baseURL.startsWith('http')
        ? api.defaults.baseURL.replace(/\/api\/v1$/, '')
        : window.location.origin;

    const fetchSystems = async () => {
        try {
            const res = await api.get('/audits/systems');
            setSystems(res.data);
            if (res.data.length > 0) setSelectedSystem(res.data[0].id);
        } catch (error) {
            toast.error("Failed to fetch systems");
        }
    };

    useEffect(() => {
        fetchSystems();
    }, []);

    // IP Address validation (IPv4 and IPv6)
    const validateIPAddress = (ip) => {
        // IPv4 pattern
        const ipv4Pattern = /^(\d{1,3}\.){3}\d{1,3}$/;
        if (ipv4Pattern.test(ip)) {
            const parts = ip.split('.');
            return parts.every(part => parseInt(part) <= 255);
        }
        
        // IPv6 pattern (simplified)
        const ipv6Pattern = /^(([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4})$/;
        return ipv6Pattern.test(ip);
    };

    const validateForm = () => {
        const newErrors = {};

        if (!newSystem.hostname.trim()) {
            newErrors.hostname = "Hostname is required";
        } else if (newSystem.hostname.trim().length < 2) {
            newErrors.hostname = "Hostname must be at least 2 characters";
        } else if (newSystem.hostname.length > 255) {
            newErrors.hostname = "Hostname must not exceed 255 characters";
        }

        if (!newSystem.ip_address.trim()) {
            newErrors.ip_address = "IP address is required";
        } else if (!validateIPAddress(newSystem.ip_address)) {
            newErrors.ip_address = "Please enter a valid IPv4 or IPv6 address";
        }

        const validOS = ['windows', 'linux', 'macos'];
        if (!validOS.includes(newSystem.operating_system.toLowerCase())) {
            newErrors.operating_system = "Invalid operating system";
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleAddSystem = async (e) => {
        e.preventDefault();
        
        if (!validateForm()) {
            toast.error("Please fix the errors in the form");
            return;
        }

        try {
            await api.post('/audits/systems', newSystem);
            toast.success("System added successfully!");
            setNewSystem({ hostname: '', operating_system: 'windows', ip_address: '' });
            setErrors({});
            fetchSystems(); // Refresh list
        } catch (error) {
            const errorMessage = error.response?.data?.detail || "Failed to add system";
            toast.error(errorMessage);
        }
    };

    const handleRunAudit = async () => {
        if (!selectedSystem) return toast.warning("Please select a system first.");
        
        setIsAuditing(true);
        try {
            toast.info("Audit started. This may take a few seconds...");
            await api.post('/audits/run', { system_id: selectedSystem });
            toast.success("Audit completed successfully!");
            navigate('/history');
        } catch (error) {
            toast.error("Audit failed.");
        } finally {
            setIsAuditing(false);
        }
    };

    return (
        <div>
            <Navbar />
            <div className="d-flex">
                <Sidebar />
                <div className="flex-grow-1 p-4">
                    <h2>Run Audit</h2>
                    
                    <div className="row mt-4">
                        <div className="col-md-6">
                            <div className="card p-4 mb-4">
                                <h4>Add New System</h4>
                                <form onSubmit={handleAddSystem}>
                                    <div className="mb-2">
                                        <label>Hostname</label>
                                        <input 
                                            type="text" 
                                            className={`form-control ${errors.hostname ? 'is-invalid' : ''}`}
                                            value={newSystem.hostname} 
                                            onChange={(e) => {
                                                setNewSystem({...newSystem, hostname: e.target.value});
                                                if (errors.hostname) setErrors({...errors, hostname: ''});
                                            }} 
                                            required 
                                        />
                                        {errors.hostname && (
                                            <div className="invalid-feedback d-block">
                                                {errors.hostname}
                                            </div>
                                        )}
                                    </div>
                                    <div className="mb-2">
                                        <label>IP Address</label>
                                        <input 
                                            type="text" 
                                            className={`form-control ${errors.ip_address ? 'is-invalid' : ''}`}
                                            value={newSystem.ip_address} 
                                            onChange={(e) => {
                                                setNewSystem({...newSystem, ip_address: e.target.value});
                                                if (errors.ip_address) setErrors({...errors, ip_address: ''});
                                            }} 
                                            placeholder="e.g., 192.168.1.1"
                                            required 
                                        />
                                        {errors.ip_address && (
                                            <div className="invalid-feedback d-block">
                                                {errors.ip_address}
                                            </div>
                                        )}
                                    </div>
                                    <div className="mb-3">
                                        <label>Operating System</label>
                                        <select 
                                            className={`form-select ${errors.operating_system ? 'is-invalid' : ''}`}
                                            value={newSystem.operating_system} 
                                            onChange={(e) => {
                                                setNewSystem({...newSystem, operating_system: e.target.value});
                                                if (errors.operating_system) setErrors({...errors, operating_system: ''});
                                            }}
                                        >
                                            <option value="windows">Windows</option>
                                            <option value="linux">Linux</option>
                                            <option value="macos">macOS</option>
                                        </select>
                                        {errors.operating_system && (
                                            <div className="invalid-feedback d-block">
                                                {errors.operating_system}
                                            </div>
                                        )}
                                    </div>
                                    <button type="submit" className="btn btn-outline-primary">Add System</button>
                                </form>
                            </div>
                        </div>

                        <div className="col-md-6">
                            <div className="card p-4">
                                <h4>Execute Audit</h4>
                                <p className="text-muted">Select a registered system to run the CIS compliance audit script.</p>
                                <select className="form-select mb-3" value={selectedSystem} onChange={(e) => setSelectedSystem(e.target.value)}>
                                    <option value="" disabled>Select a system...</option>
                                    {systems.map(sys => (
                                        <option key={sys.id} value={sys.id}>{sys.hostname} ({sys.operating_system})</option>
                                    ))}
                                </select>
                                <button className="btn btn-primary" onClick={handleRunAudit} disabled={isAuditing || systems.length === 0}>
                                    {isAuditing ? 'Auditing in progress...' : 'Run Audit Now'}
                                </button>
                            </div>
                        </div>
                    </div>
                    <div className="row mt-3">
                        <div className="col-12">
                            <div className="card p-4">
                                <h4>Download Local Auditor Script</h4>
                                <p className="text-muted">Download a lightweight audit script for Linux or Windows, then run it locally as root/admin to upload audit results automatically.</p>
                                <div className="d-flex flex-column gap-3 mb-3">
                                    <div>
                                        <strong>Linux Script:</strong>
                                        <a
                                            href={`${backendBaseUrl}/api/v1/audits/download-script/linux`}
                                            className="btn btn-outline-primary btn-sm ms-2 me-2"
                                            download="audit.sh"
                                        >
                                            Download Linux Script
                                        </a>
                                        <span className="text-muted small">({`${backendBaseUrl}/api/v1/audits/download-script/linux`})</span>
                                    </div>
                                    <div>
                                        <strong>Windows Script:</strong>
                                        <a
                                            href={`${backendBaseUrl}/api/v1/audits/download-script/windows`}
                                            className="btn btn-outline-primary btn-sm ms-2 me-2"
                                            download="audit.ps1"
                                        >
                                            Download Windows Script
                                        </a>
                                        <span className="text-muted small">({`${backendBaseUrl}/api/v1/audits/download-script/windows`})</span>
                                    </div>
                                </div>
                                <p className="text-muted mb-1"><strong>Example usage:</strong></p>
                                <pre className="bg-light p-2 rounded"><code>bash audit.sh --api-url {backendBaseUrl}/api/v1 --token &lt;JWT&gt; --hostname myhost --operating_system linux --ip_address 192.168.1.10</code></pre>
                                <pre className="bg-light p-2 rounded mt-2"><code>powershell -ExecutionPolicy Bypass -File audit.ps1 -ApiUrl {backendBaseUrl}/api/v1 -Token &lt;JWT&gt; -Hostname myhost -OperatingSystem windows -IpAddress 192.168.1.10</code></pre>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default RunAudit;
