import React from 'react';

const ResponsiveTest = () => {
  return (
    <div style={{ 
      padding: '1rem', 
      background: '#f0f0f0', 
      border: '2px solid #333',
      margin: '1rem',
      borderRadius: '8px'
    }}>
      <h3>Responsive Design Test</h3>
      <p>This component helps verify that the responsive design is working correctly.</p>
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '1rem',
        marginTop: '1rem'
      }}>
        <div style={{ background: '#fff', padding: '1rem', borderRadius: '4px' }}>
          <strong>Card 1</strong>
          <p>This should wrap to new lines on smaller screens</p>
        </div>
        <div style={{ background: '#fff', padding: '1rem', borderRadius: '4px' }}>
          <strong>Card 2</strong>
          <p>Grid should adapt to screen size</p>
        </div>
        <div style={{ background: '#fff', padding: '1rem', borderRadius: '4px' }}>
          <strong>Card 3</strong>
          <p>No horizontal overflow should occur</p>
        </div>
      </div>
    </div>
  );
};

export default ResponsiveTest; 