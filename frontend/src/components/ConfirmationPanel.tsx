import React from 'react';
import { AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

interface ConfirmationPanelProps {
  summary: string;
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
}

export const ConfirmationPanel: React.FC<ConfirmationPanelProps> = ({
  summary,
  onConfirm,
  onCancel,
  loading
}) => {
  return (
    <div className="confirmation-box">
      <div className="confirmation-header">
        <AlertTriangle size={17} />
        <span>Confirm this action</span>
      </div>
      <div className="confirmation-summary">
        {summary}
      </div>
      <div className="confirmation-actions">
        <button
          className="btn-confirm"
          onClick={onConfirm}
          disabled={loading}
        >
          <CheckCircle size={15} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'text-bottom' }} />
          Yes, submit it
        </button>
        <button
          className="btn-cancel"
          onClick={onCancel}
          disabled={loading}
        >
          <XCircle size={15} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'text-bottom' }} />
          No, cancel
        </button>
      </div>
    </div>
  );
};
