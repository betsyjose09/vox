import React, { useState, useEffect } from 'react';
import { Home } from './pages/Home';
import { Assistant } from './pages/Assistant';
import { History } from './pages/History';
import { createSession } from './lib/api';
import { Home as HomeIcon, MessageSquare, History as HistoryIcon } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'home' | 'assistant' | 'history'>('assistant');
  const [sessionId, setSessionId] = useState<string>('');

  // Single shared session across tabs so Audit History reflects the active identity
  useEffect(() => {
    createSession()
      .then((sess) => setSessionId(sess.session_id))
      .catch((e) => console.error('Session creation failed:', e));
  }, []);

  return (
    <>
      <header className="masthead">
        <div className="masthead-inner">
          <div className="brand">
            <img src="/knotopian-logo.webp" alt="Knotopian" className="masthead-logo" />
            <span className="logo-badge">KIT VOX</span>
          </div>

          <nav className="nav-links">
            <button
              className={`nav-btn ${activeTab === 'home' ? 'active' : ''}`}
              onClick={() => setActiveTab('home')}
            >
              Home
            </button>
            <button
              className={`nav-btn ${activeTab === 'assistant' ? 'active' : ''}`}
              onClick={() => setActiveTab('assistant')}
            >
              Assistant
            </button>
            <button
              className={`nav-btn ${activeTab === 'history' ? 'active' : ''}`}
              onClick={() => setActiveTab('history')}
            >
              Audit trail
            </button>
          </nav>
        </div>
      </header>

      <div className="app-container">
        <main style={{ flex: 1 }}>
          {activeTab === 'home' && <Home onNavigateToAssistant={() => setActiveTab('assistant')} />}
          {activeTab === 'assistant' && (
            <Assistant sessionId={sessionId} onSessionChange={setSessionId} />
          )}
          {activeTab === 'history' && <History sessionId={sessionId} />}
        </main>

        <footer className="app-footer">
          <div>
            Voice replies are pre-recorded audio. Actions that change college data always ask for confirmation first.
          </div>
          <div>
            Knotopian Institute of Technology, Coimbatore
          </div>
        </footer>
      </div>
    </>
  );
};
