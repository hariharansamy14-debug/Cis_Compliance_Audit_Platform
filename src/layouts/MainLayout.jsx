import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from '../components/Sidebar/Sidebar';
import Topbar from '../components/Topbar/Topbar';

const MainLayout = () => {
    const [collapsed, setCollapsed] = useState(false);

    const toggleSidebar = () => {
        setCollapsed(prev => !prev);
    };

    return (
        <div className="app-container">
            <Sidebar collapsed={collapsed} toggleSidebar={toggleSidebar} />
            <div className={`content-wrapper ${collapsed ? 'collapsed' : ''}`}>
                <Topbar toggleSidebar={toggleSidebar} collapsed={collapsed} />
                <main className="main-content animate-fade-in">
                    <Outlet />
                </main>
            </div>
        </div>
    );
};

export default MainLayout;
```
