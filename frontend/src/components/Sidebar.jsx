export default function Sidebar({
    sessions,
    activeSession,
    onSelectSession,
    onNewChat,
    onDeleteSession,
}) {
    return (
        <aside className="sidebar">
            {/* Header */}
            <div className="sidebar-header">
                <div className="sidebar-logo">🤖</div>
                <span className="sidebar-title">Travel AI</span>
            </div>

            {/* New chat */}
            <button className="new-chat-btn" onClick={onNewChat}>
                ＋ Cuộc trò chuyện mới
            </button>

            {/* Session list */}
            {sessions.length > 0 && (
                <div className="sidebar-label">Lịch sử</div>
            )}

            <div className="session-list">
                {sessions.map((s) => (
                    <div
                        key={s.session_id}
                        className={`session-item ${s.session_id === activeSession ? 'active' : ''}`}
                        onClick={() => onSelectSession(s.session_id)}
                    >
                        <span className="session-icon">💬</span>
                        <span className="session-item-title">{s.title}</span>
                        <button
                            className="session-delete-btn"
                            onClick={(e) => {
                                e.stopPropagation();
                                onDeleteSession(s.session_id);
                            }}
                            title="Xóa"
                        >
                            ✕
                        </button>
                    </div>
                ))}
            </div>
        </aside>
    );
}
