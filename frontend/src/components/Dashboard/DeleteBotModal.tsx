import React, { useState } from 'react';
import { X, AlertTriangle, DollarSign } from 'lucide-react';

interface DeleteBotModalProps {
  isOpen: boolean;
  botName: string;
  onConfirm: (liquidate: boolean) => void;
  onCancel: () => void;
}

export const DeleteBotModal: React.FC<DeleteBotModalProps> = ({
  isOpen,
  botName,
  onConfirm,
  onCancel
}) => {
  const [liquidate, setLiquidate] = useState(true); // Default to true

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            <h3 className="text-lg font-semibold text-gray-900">Delete Bot</h3>
          </div>
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-4 space-y-4">
          <p className="text-gray-700">
            Are you sure you want to delete bot <span className="font-semibold">{botName}</span>?
          </p>

          {/* Liquidate Checkbox */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <label className="flex items-start space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={liquidate}
                onChange={(e) => setLiquidate(e.target.checked)}
                className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <DollarSign className="h-4 w-4 text-blue-600" />
                  <span className="font-medium text-gray-900">Liquidate holdings</span>
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  Sell all holdings for this trading pair before deleting the bot
                </p>
              </div>
            </label>
          </div>

          {!liquidate && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <p className="text-sm text-yellow-800">
                <strong>Warning:</strong> Any holdings for this trading pair will remain in your account.
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-3 p-4 border-t bg-gray-50">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={() => onConfirm(liquidate)}
            className="px-4 py-2 bg-red-600 text-white hover:bg-red-700 rounded-lg transition-colors font-medium"
          >
            {liquidate ? 'Liquidate & Delete' : 'Delete Bot'}
          </button>
        </div>
      </div>
    </div>
  );
};
