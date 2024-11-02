import React, { useState, useEffect } from 'react';
import GridLayout from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import './home.css';
import '../components/common/common.css';

const Home = () => {
  const username = localStorage.getItem('username');
  
  const [layout, setLayout] = useState([]);
  const [showWidgetConfig, setShowWidgetConfig] = useState(false);
  const [overdueServices, setOverdueServices] = useState([]);
  const [dueServices, setDueServices] = useState([]);

  const fetchOverdueServices = async () => {
    try {
      const baseUrl = import.meta.env.VITE_BASE_URL;
      const response = await fetch(`${baseUrl}/services/services_overdue`, {
        method: 'GET',
        credentials: 'include',
      });
      if (!response.ok) {
        const errorData = await response.text(); // Fetching as text to inspect
        console.error('Error fetching overdue services:', errorData);
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setOverdueServices(data.services_overdue);
    } catch (error) {
      console.error('Failed to fetch overdue services:', error);
    }
  };
  
  const fetchDueServices = async () => {
    try {
      const baseUrl = import.meta.env.VITE_BASE_URL;
      const response = await fetch(`${baseUrl}/services/service/due_30_days`, {
        method: 'GET',
        credentials: 'include',
      });
      if (!response.ok) {
        const errorData = await response.text(); // Fetching as text to inspect
        console.error('Error fetching services due in 30 days:', errorData);
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setDueServices(data.services_due);
    } catch (error) {
      console.error('Failed to fetch services due in 30 days:', error);
    }
  };
  
  

  useEffect(() => {
    fetchOverdueServices();
    fetchDueServices();
    
    const savedLayout = localStorage.getItem('dashboardLayout');
    if (savedLayout) {
      setLayout(JSON.parse(savedLayout));
    } else {
      setLayout([
        { i: 'services', x: 0, y: 0, w: 4, h: 3 },
        { i: 'overdueServices', x: 4, y: 0, w: 4, h: 3 },
        { i: 'costChart', x: 0, y: 3, w: 8, h: 4 },
      ]);
    }
  }, []);

  const handleLayoutChange = (newLayout) => {
    setLayout(newLayout);
    localStorage.setItem('dashboardLayout', JSON.stringify(newLayout));
  };

  const addWidget = () => {
    setShowWidgetConfig(true);
  };

  const configureWidget = (widgetType) => {
    const newWidgetId = `${widgetType}-${Date.now()}`;
    const newWidget = {
      i: newWidgetId,
      x: 0,
      y: Infinity,
      w: 4,
      h: 3,
    };
    const updatedLayout = [...layout, newWidget];
    setLayout(updatedLayout);
    handleLayoutChange(updatedLayout);
    setShowWidgetConfig(false);
  };

  const removeWidget = (id, e) => {
    e.stopPropagation();
    const updatedLayout = layout.filter((item) => item.i !== id);
    setLayout(updatedLayout);
    handleLayoutChange(updatedLayout);
  };

  const resetWidgets = () => {
    setLayout([]);
    localStorage.removeItem('dashboardLayout');
  };

  const renderServiceList = (services) => (
    <div className="widget-content" style={{ maxHeight: '200px', overflowY: 'auto' }}>
      <ul>
        {services.map((service) => (
          <li key={service.id}>
            {service.service_type} - {service.service_date}
          </li>
        ))}
      </ul>
    </div>
  );

  const widgets = {
    services: (
      <div className="widget-content">
        <h4>Services Due in 30 Days</h4>
        {renderServiceList(dueServices)}
      </div>
    ),
    overdueServices: (
      <div className="widget-content">
        <h4>Overdue Services</h4>
        {renderServiceList(overdueServices)}
      </div>
    ),
    costChart: (
      <div className="widget-content">
        <h4>Total Costs (Last 30 Days)</h4>
      </div>
    ),
  };

  return (
    <div>
      <h2>Welcome, {username} to MATER!</h2>
      <h3>Your Dashboard</h3>

      <button className='standard-btn' onClick={addWidget}>Add Widget</button>
      <button className='standard-del-btn' onClick={resetWidgets} style={{ marginLeft: '10px' }}>
        Reset Widgets
      </button>

      {showWidgetConfig && (
        <div className="widget-config-modal">
          <h4>Select a Widget Type</h4>
          <ul>
            <li onClick={() => configureWidget('costChart')}>Total Costs (Last 30 Days)</li>
            <li onClick={() => configureWidget('services')}>Services Due in the Next 30 Days</li>
            <li onClick={() => configureWidget('overdueServices')}>Overdue Services</li>
            <li onClick={() => configureWidget('newestAssets')}>Newest Assets</li>
          </ul>
          <button className='standard-del-btn' onClick={() => setShowWidgetConfig(false)}>Cancel</button>
        </div>
      )}

      <GridLayout
        className="layout"
        layout={layout}
        cols={12}
        rowHeight={30}
        width={1200}
        onLayoutChange={handleLayoutChange}
        isDraggable={true}
        isResizable={true}
        draggableCancel=".remove-btn" // Prevent drag when interacting with elements with this class
      >
        {layout.map((item) => (
          <div key={item.i} data-grid={{ ...item }} className="widget">
            <button
              onClick={(e) => removeWidget(item.i, e)}
              className="remove-btn"
            >
              Remove
            </button>
            {widgets[item.i.split('-')[0]]}
          </div>
        ))}
      </GridLayout>
    </div>
  );
};

export default Home;
