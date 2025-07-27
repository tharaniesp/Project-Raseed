// src/components/Upload/UploadComponent.js
import React, { useState, useRef, useEffect } from 'react';
import { Upload, Camera, CheckCircle, AlertCircle, Loader, X, Eye, MessageSquare, Video } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { uploadReceipt } from '../../services/receiptService';
import { useReceipt } from '../../context/ReceiptContext';
import './UploadComponent.css';

const UploadComponent = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [message, setMessage] = useState({ text: '', type: '' });
  const [dragActive, setDragActive] = useState(false);
  const [uploadedReceiptId, setUploadedReceiptId] = useState(null);
  const [showCamera, setShowCamera] = useState(false);
  const [cameraStream, setCameraStream] = useState(null);
  const fileInputRef = useRef(null);
  const cameraRef = useRef(null);
  const navigate = useNavigate();
  
  // 🔧 FIX: Access addReceipt from actions
  const { actions } = useReceipt();
  const { addReceipt } = actions;

  const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'video/mp4', 'video/webm'];
  const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const showMessage = (text, type = 'success') => {
    setMessage({ text, type });
    setTimeout(() => setMessage({ text: '', type: '' }), 8000);
  };

  const validateFile = (file) => {
    if (!ALLOWED_TYPES.includes(file.type)) {
      throw new Error('Invalid file type. Please select an image or video file.');
    }
    
    if (file.size > MAX_FILE_SIZE) {
      throw new Error('File size must be less than 10MB');
    }
    
    return true;
  };

  const handleFileSelect = (file) => {
    if (!file) return;

    try {
      validateFile(file);
      setSelectedFile(file);
      setUploadedReceiptId(null); // Reset uploaded receipt ID

      // Create preview for images
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => setPreview(e.target.result);
        reader.readAsDataURL(file);
      } else {
        setPreview(null);
      }
    } catch (error) {
      showMessage(error.message, 'error');
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const files = e.dataTransfer.files;
    if (files && files[0]) {
      handleFileSelect(files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setUploadProgress(0);

    try {
      const result = await uploadReceipt(selectedFile, (progress) => {
        setUploadProgress(progress);
      });

      console.log('✅ Upload result:', result); // Debug log
      
      // Store the uploaded receipt ID
      setUploadedReceiptId(result.receipt_id);
      
      showMessage(`✅ Upload successful! Receipt ID: ${result.receipt_id}`, 'success');
      
      // 🔧 This should now work properly
      addReceipt(result);
      
      // Reset form
      resetForm();
      
    } catch (error) {
      console.error('Upload error:', error);
      showMessage(`Upload failed: ${error.message}`, 'error');
    } finally {
      setUploading(false);
    }
  };

  const resetForm = () => {
    setSelectedFile(null);
    setPreview(null);
    setUploadProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeFile = () => {
    resetForm();
    setMessage({ text: '', type: '' });
    setUploadedReceiptId(null);
  };

  const viewReceipts = () => {
    navigate('/receipts');
  };

  const askQuestions = () => {
    navigate('/query');
  };

  // Camera functionality
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          facingMode: 'environment', // Use back camera if available
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        } 
      });
      setCameraStream(stream);
      setShowCamera(true);
    } catch (error) {
      showMessage('Camera access denied. Please allow camera permissions.', 'error');
    }
  };

  const stopCamera = () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach(track => track.stop());
      setCameraStream(null);
    }
    setShowCamera(false);
  };

  const capturePhoto = () => {
    if (!cameraRef.current) return;

    const canvas = document.createElement('canvas');
    const video = cameraRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);
    
    canvas.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], `receipt_${Date.now()}.jpg`, { type: 'image/jpeg' });
        handleFileSelect(file);
        stopCamera();
      }
    }, 'image/jpeg', 0.9);
  };

  // Handle camera stream when video element is ready
  useEffect(() => {
    if (cameraRef.current && cameraStream) {
      cameraRef.current.srcObject = cameraStream;
    }
  }, [cameraStream]);

  // Cleanup camera stream on unmount
  useEffect(() => {
    return () => {
      if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
      }
    };
  }, [cameraStream]);

  return (
    <div className="upload-component">
      {/* <div className="upload-header">
        <h2>Upload Receipt</h2>
        <p>Upload your receipt photos or videos to extract data automatically</p>
      </div> */}

      {/* Upload Area */}
      {!showCamera ? (
        <div
          className={`upload-area ${dragActive ? 'drag-active' : ''} ${selectedFile ? 'has-file' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => !selectedFile && fileInputRef.current?.click()}
        >
          {!selectedFile ? (
            <>
              <Camera className="upload-icon" size={48} />
              <h3>Upload Receipt Photo</h3>
              <p>Drag & drop or click to select</p>
              <span className="file-types">JPG, PNG, GIF, WebP, MP4, WebM (max 10MB)</span>
              
              {/* Camera Button */}
              <button 
                className="camera-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  startCamera();
                }}
              >
                <Video size={20} />
                <span>Take Photo</span>
              </button>
            </>
          ) : (
            <div className="file-selected">
              <CheckCircle className="success-icon" size={48} />
              <h3>File Ready</h3>
              <p>{selectedFile.name}</p>
            </div>
          )}
          
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*,video/*"
            className="file-input"
            onChange={(e) => handleFileSelect(e.target.files[0])}
          />
        </div>
      ) : (
        /* Camera Interface */
        <div className="camera-interface">
          <div className="camera-header">
            <h3>Take Receipt Photo</h3>
            <button className="close-camera-btn" onClick={stopCamera}>
              <X size={20} />
            </button>
          </div>
          
          <div className="camera-container">
            <video
              ref={cameraRef}
              autoPlay
              playsInline
              muted
              className="camera-video"
            />
            
            <div className="camera-overlay">
              <div className="camera-frame">
                <div className="corner top-left"></div>
                <div className="corner top-right"></div>
                <div className="corner bottom-left"></div>
                <div className="corner bottom-right"></div>
              </div>
            </div>
          </div>
          
          <div className="camera-controls">
            <button className="capture-btn" onClick={capturePhoto}>
              <Camera size={24} />
              <span>Capture</span>
            </button>
          </div>
        </div>
      )}

      {/* Preview Area */}
      {selectedFile && (
        <div className="preview-area">
          {preview && (
            <div className="preview-container">
              <img src={preview} alt="Receipt preview" className="preview-image" />
            </div>
          )}
          
          <div className="file-info">
            <div className="file-details">
              <div className="file-name">{selectedFile.name}</div>
              <div className="file-meta">
                <span className="file-size">{formatFileSize(selectedFile.size)}</span>
                <span className="file-type">{selectedFile.type}</span>
              </div>
            </div>
            <button className="remove-btn" onClick={removeFile} disabled={uploading}>
              <X size={16} />
            </button>
          </div>

          {/* Upload Button */}
          <button
            className={`upload-btn ${uploading ? 'uploading' : ''}`}
            onClick={handleUpload}
            disabled={uploading}
          >
            {uploading ? (
              <>
                <Loader className="spinner" size={20} />
                <span>Uploading...</span>
              </>
            ) : (
              <>
                <Upload size={20} />
                <span>Upload Receipt</span>
              </>
            )}
          </button>

          {/* Progress Bar */}
          {uploading && (
            <div className="progress-container">
              <div className="progress-bar">
                <div 
                  className="progress-fill"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
              <span className="progress-text">{Math.round(uploadProgress)}%</span>
            </div>
          )}
        </div>
      )}

      {/* Success Actions */}
      {uploadedReceiptId && (
        <div className="success-actions">
          <div className="success-message">
            <CheckCircle size={20} />
            <span>Receipt uploaded successfully! What would you like to do next?</span>
          </div>
          <div className="action-buttons">
            <button className="action-btn primary" onClick={viewReceipts}>
              <Eye size={16} />
              <span>View My Receipts</span>
            </button>
            <button className="action-btn secondary" onClick={askQuestions}>
              <MessageSquare size={16} />
              <span>Ask Questions</span>
            </button>
          </div>
        </div>
      )}

      {/* Status Message */}
      {message.text && !uploadedReceiptId && (
        <div className={`status-message ${message.type}`}>
          {message.type === 'success' ? (
            <CheckCircle size={20} />
          ) : (
            <AlertCircle size={20} />
          )}
          <span>{message.text}</span>
        </div>
      )}
    </div>
  );
};

export default UploadComponent;