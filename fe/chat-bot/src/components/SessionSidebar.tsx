import React from 'react';
import { type Session } from '../types/chat';

interface SessionSidebarProps {
  sessions: Session[];
  activeSessionId: string;
  onSelectSession: (sessionId: string) => void;
  onNewChat: () => void;
  onDeleteSession: (sessionId: string) => void;
}

export const SessionSidebar: React.FC<SessionSidebarProps> = ({
  sessions = [],
  activeSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession
}) => {
  const safeSessions = Array.isArray(sessions) ? sessions : [];
  return (
    <div className="session-sidebar">
      <div className="session-sidebar-header">
        <h2 className="session-sidebar-title">Chats</h2>
        <button className="new-chat-button" onClick={onNewChat} aria-label="New Chat">
          + New
        </button>
      </div>
      <div className="session-list">
        {safeSessions.map((session) => (
          <div
            key={session.id}
            className={`session-item ${session.id === activeSessionId ? 'session-item--active' : ''}`}
            onClick={() => onSelectSession(session.id)}
          >
            <span className="session-item-title" title={session.title}>{session.title}</span>
            <button 
              className="delete-session-button" 
              onClick={(e) => { e.stopPropagation(); onDeleteSession(session.id); }}
              title="Delete chat"
            >
              ×
            </button>
          </div>
        ))}
        {safeSessions.length === 0 && (
          <div className="session-empty">No previous chats.</div>
        )}
      </div>
    </div>
  );
};
