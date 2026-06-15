export default function TypingIndicator({ status }) {
    return (
        <div className="typing-row">
            <div className="bubble-avatar assistant">
                <span className="material-symbols-outlined icon-fill">smart_toy</span>
            </div>
            <div className="typing-indicator" aria-label="Đang xử lý">
                <div style={{ display: 'flex', gap: '5px' }}>
                    <div className="typing-dot" />
                    <div className="typing-dot" />
                    <div className="typing-dot" />
                </div>
                {status && (
                    <span style={{ fontSize: '12px', color: 'var(--on-surface-variant)', fontWeight: 600, marginLeft: '4px', whiteSpace: 'nowrap' }}>
                        {status}
                    </span>
                )}
            </div>
        </div>
    );
}
