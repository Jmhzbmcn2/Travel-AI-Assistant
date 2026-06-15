import { useState, useEffect } from 'react';

export default function Sidebar({
    sessions,
    activeSession,
    onSelectSession,
    onNewChat,
    onDeleteSession,
    onRenameSession,
}) {
    const [activeMenuSessionId, setActiveMenuSessionId] = useState(null);
    const [editingSessionId, setEditingSessionId] = useState(null);
    const [renameText, setRenameText] = useState('');

    // Close menu when clicking outside
    useEffect(() => {
        const handleClickOutside = () => {
            setActiveMenuSessionId(null);
        };
        document.addEventListener('click', handleClickOutside);
        return () => document.removeEventListener('click', handleClickOutside);
    }, []);

    const handleMenuToggle = (e, sid) => {
        e.stopPropagation();
        setActiveMenuSessionId(activeMenuSessionId === sid ? null : sid);
    };

    const handleStartRename = (e, session) => {
        e.stopPropagation();
        setEditingSessionId(session.session_id);
        setRenameText(session.title);
        setActiveMenuSessionId(null);
    };

    const handleSaveRename = (sid) => {
        if (renameText.trim() && renameText !== sessions.find(s => s.session_id === sid)?.title) {
            onRenameSession(sid, renameText.trim());
        }
        setEditingSessionId(null);
    };

    const handleCancelRename = () => {
        setEditingSessionId(null);
    };

    const visibleSessions = sessions.length
        ? sessions
        : [
            { session_id: 'sample-da-nang', title: 'Đà Nẵng 4N3Đ', sample: true },
            { session_id: 'sample-phu-quoc', title: 'Phú Quốc 3N2Đ', sample: true },
        ];

    return (
        <aside className="sidebar">
            <div className="sidebar-brand">
                <span className="material-symbols-outlined icon-fill">travel_explore</span>
                <div>
                    <h1>Travel AI</h1>
                    <p>Vietnam Premium</p>
                </div>
            </div>

            <button className="new-chat-btn" type="button" onClick={onNewChat}>
                <span className="material-symbols-outlined">add</span>
                Chuyến đi mới
            </button>

            <nav className="recent-trips" aria-label="Gần đây">
                <p>Gần đây</p>
                <ul>
                    {visibleSessions.map((session, index) => {
                        const isActive = session.session_id === activeSession || (!activeSession && index === 0);
                        const isEditing = session.session_id === editingSessionId;
                        const isMenuOpen = session.session_id === activeMenuSessionId;

                        return (
                            <li key={session.session_id} className="session-item-container">
                                {isEditing ? (
                                    <div className="rename-input-wrapper">
                                        <input
                                            type="text"
                                            className="session-rename-input"
                                            value={renameText}
                                            onChange={(e) => setRenameText(e.target.value)}
                                            onKeyDown={(e) => {
                                                if (e.key === 'Enter') handleSaveRename(session.session_id);
                                                if (e.key === 'Escape') handleCancelRename();
                                            }}
                                            onBlur={() => handleSaveRename(session.session_id)}
                                            autoFocus
                                        />
                                    </div>
                                ) : (
                                    <>
                                        <button
                                            type="button"
                                            className={`session-btn ${isActive ? 'active' : ''}`}
                                            onClick={() => {
                                                if (!session.sample) onSelectSession(session.session_id);
                                            }}
                                        >
                                            <span className="material-symbols-outlined">history</span>
                                            <span className="session-title-text">{session.title}</span>
                                        </button>

                                        {!session.sample && (
                                            <div className="session-actions-wrapper">
                                                <button
                                                    className="session-menu-trigger"
                                                    type="button"
                                                    onClick={(e) => handleMenuToggle(e, session.session_id)}
                                                    title="Tùy chọn"
                                                >
                                                    <span className="material-symbols-outlined">more_vert</span>
                                                </button>

                                                {isMenuOpen && (
                                                    <div className="session-dropdown-menu">
                                                        <button
                                                            type="button"
                                                            onClick={(e) => handleStartRename(e, session)}
                                                        >
                                                            <span className="material-symbols-outlined">edit</span>
                                                            Đổi tên
                                                        </button>
                                                        <button
                                                            type="button"
                                                            className="delete-item"
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                onDeleteSession(session.session_id);
                                                                setActiveMenuSessionId(null);
                                                            }}
                                                        >
                                                            <span className="material-symbols-outlined">delete</span>
                                                            Xóa
                                                        </button>
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                    </>
                                )}
                            </li>
                        );
                    })}
                </ul>
            </nav>

            <div className="sidebar-footer">
                <button type="button">
                    <span className="material-symbols-outlined">settings</span>
                    Cài đặt
                </button>
                <button type="button">
                    <span className="material-symbols-outlined">help</span>
                    Trợ giúp
                </button>
            </div>
        </aside>
    );
}
