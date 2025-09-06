import React, { createContext, useContext, useState, useCallback } from 'react';

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  title: string;
  message: string;
  duration?: number; // milliseconds, 0 means no auto-dismiss
  actions?: Array<{
    label: string;
    action: () => void;
    style?: 'primary' | 'secondary';
  }>;
}

interface ToastContextType {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => string;
  removeToast: (id: string) => void;
  clearToasts: () => void;
}

const ToastContext = createContext<ToastContextType | null>(null);

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const newToast: Toast = {
      ...toast,
      id,
      duration: toast.duration ?? 5000, // Default 5 seconds
    };

    setToasts(prev => [...prev, newToast]);

    // Auto-dismiss if duration > 0
    if (newToast.duration && newToast.duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, newToast.duration);
    }

    return id;
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  const clearToasts = useCallback(() => {
    setToasts([]);
  }, []);

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast, clearToasts }}>
      {children}
      <ToastContainer />
    </ToastContext.Provider>
  );
};

const getToastIcon = (type: Toast['type']) => {
  switch (type) {
    case 'success':
      return '✅';
    case 'error':
      return '❌';
    case 'warning':
      return '⚠️';
    case 'info':
      return 'ℹ️';
    default:
      return '📢';
  }
};

const getToastStyles = (type: Toast['type']) => {
  switch (type) {
    case 'success':
      return 'bg-green-50 border-green-200 text-green-800';
    case 'error':
      return 'bg-red-50 border-red-200 text-red-800';
    case 'warning':
      return 'bg-yellow-50 border-yellow-200 text-yellow-800';
    case 'info':
      return 'bg-blue-50 border-blue-200 text-blue-800';
    default:
      return 'bg-gray-50 border-gray-200 text-gray-800';
  }
};

const ToastItem: React.FC<{ toast: Toast }> = ({ toast }) => {
  const { removeToast } = useToast();

  return (
    <div className={`border rounded-lg p-4 shadow-lg max-w-md w-full transform transition-all duration-300 ease-in-out ${getToastStyles(toast.type)}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3 flex-1">
          <span className="text-lg">{getToastIcon(toast.type)}</span>
          <div className="flex-1">
            <h4 className="font-medium text-sm">{toast.title}</h4>
            <p className="text-sm mt-1 opacity-90">{toast.message}</p>
            
            {toast.actions && toast.actions.length > 0 && (
              <div className="flex space-x-2 mt-3">
                {toast.actions.map((action, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      action.action();
                      removeToast(toast.id);
                    }}
                    className={`text-xs px-3 py-1 rounded ${
                      action.style === 'primary'
                        ? 'bg-white bg-opacity-80 hover:bg-opacity-100 font-medium'
                        : 'bg-white bg-opacity-50 hover:bg-opacity-70'
                    }`}
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
        
        <button
          onClick={() => removeToast(toast.id)}
          className="text-lg opacity-60 hover:opacity-100 ml-2"
        >
          ×
        </button>
      </div>
    </div>
  );
};

const ToastContainer: React.FC = () => {
  const { toasts } = useToast();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {toasts.map(toast => (
        <ToastItem key={toast.id} toast={toast} />
      ))}
    </div>
  );
};
