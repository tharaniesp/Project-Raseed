import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import NotificationCenter from './NotificationCenter';

// Mock WebSocket
const mockWebSocket = {
  onopen: jest.fn(),
  onmessage: jest.fn(),
  onclose: jest.fn(),
  onerror: jest.fn(),
  close: jest.fn(),
  send: jest.fn(),
  readyState: 1, // WebSocket.OPEN
};

global.WebSocket = jest.fn(() => mockWebSocket);

describe('NotificationCenter', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders notification bell', () => {
    render(<NotificationCenter />);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  test('opens notification panel when bell is clicked', () => {
    render(<NotificationCenter />);
    const bell = screen.getByRole('button');
    
    fireEvent.click(bell);
    
    expect(screen.getByText('Notifications')).toBeInTheDocument();
  });

  test('closes notification panel when clicking outside', async () => {
    render(<NotificationCenter />);
    const bell = screen.getByRole('button');
    
    // Open the panel
    fireEvent.click(bell);
    expect(screen.getByText('Notifications')).toBeInTheDocument();
    
    // Click outside the notification center
    fireEvent.mouseDown(document.body);
    
    await waitFor(() => {
      expect(screen.queryByText('Notifications')).not.toBeInTheDocument();
    });
  });

  test('closes notification panel when pressing Escape key', async () => {
    render(<NotificationCenter />);
    const bell = screen.getByRole('button');
    
    // Open the panel
    fireEvent.click(bell);
    expect(screen.getByText('Notifications')).toBeInTheDocument();
    
    // Press Escape key
    fireEvent.keyDown(document, { key: 'Escape' });
    
    await waitFor(() => {
      expect(screen.queryByText('Notifications')).not.toBeInTheDocument();
    });
  });

  test('does not close when clicking inside notification panel', () => {
    render(<NotificationCenter />);
    const bell = screen.getByRole('button');
    
    // Open the panel
    fireEvent.click(bell);
    expect(screen.getByText('Notifications')).toBeInTheDocument();
    
    // Click inside the notification panel
    const panel = screen.getByText('Notifications').closest('.notification-panel');
    fireEvent.mouseDown(panel);
    
    // Panel should still be open
    expect(screen.getByText('Notifications')).toBeInTheDocument();
  });

  test('shows connection status indicator', () => {
    render(<NotificationCenter />);
    
    // Should show connection indicator
    const indicator = screen.getByTitle('Disconnected');
    expect(indicator).toBeInTheDocument();
  });
}); 