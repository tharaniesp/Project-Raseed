// src/firebase.js
import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';
import { getAnalytics } from 'firebase/analytics';

// Your Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyDjh_5GdfaOUhzm_tCxAITrhIiBtaeDNzM",
  authDomain: "project-raseed-990b0.firebaseapp.com",
  projectId: "project-raseed-990b0",
  storageBucket: "project-raseed-990b0.firebasestorage.app",
  messagingSenderId: "438577587236",
  appId: "1:438577587236:web:fe2996830a5150da74e4b1",
  measurementId: "G-GHEP75VEPV"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Analytics
const analytics = getAnalytics(app);

// Initialize Firebase Authentication and get a reference to the service
export const auth = getAuth(app);

// Create Google Auth Provider
export const googleProvider = new GoogleAuthProvider();

// Configure Google Auth Provider
googleProvider.setCustomParameters({
  prompt: 'select_account'
});

export default app; 