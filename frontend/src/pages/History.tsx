import React, { useEffect, useState } from 'react';
import { getHistory } from '../lib/api';

export const History: React.FC<{ sessionId: string }> = ({ sessionId }) => {
  const [history, setHistory] = useState<any[]>([]);

  useEffect(() => {
    if (sessionId) {
      getHistory(sessionId).then(setHistory).catch(console.error);
    }
  }, [sessionId]);

  return (
    <div className="history-panel">
      <h3 className="panel-title">Your audit trail</h3>
      <p className="panel-lede">
        Every question and every submitted action is logged against the signed-in account, per
        college regulation 12.4. You see only this account's activity.
      </p>

      {history.length === 0 ? (
        <div className="empty-state">
          Nothing logged yet for this account. Ask the assistant something and it will appear here.
        </div>
      ) : (
        <div className="history-list">
          {history.map((turn, i) => (
            <div key={i} className="history-item">
              <div className="history-meta">
                <span>{new Date(turn.created_at).toLocaleString()}</span>
                <span className="history-intent">{turn.intent} — {turn.module}</span>
              </div>
              <div className="history-user">
                <strong>You:</strong> {turn.user_text}
              </div>
              <div className="history-reply">
                <strong>KIT VOX:</strong> {turn.assistant_text}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
