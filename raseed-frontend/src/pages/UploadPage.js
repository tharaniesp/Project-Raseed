// src/pages/UploadPage.js
import React from 'react';
import UploadComponent from '../components/Upload/UploadComponent';

const UploadPage = () => {
  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Upload Receipt</h1>
        <p className="page-description">
          Upload your receipt photos or videos to extract data automatically using AI
        </p>
      </div>
      
      <div className="page-content">
        <UploadComponent />
      </div>
    </div>
  );
};

export default UploadPage;