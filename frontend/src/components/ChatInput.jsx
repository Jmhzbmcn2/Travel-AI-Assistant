import { useEffect, useRef, useState } from 'react';

export default function ChatInput({ onSend, disabled }) {
    const [text, setText] = useState('');
    const textareaRef = useRef(null);

    useEffect(() => {
        if (!textareaRef.current) return;
        textareaRef.current.style.height = 'auto';
        textareaRef.current.style.height = `${Math.max(textareaRef.current.scrollHeight, 80)}px`;
    }, [text]);

    const handleSend = () => {
        const trimmed = text.trim();
        if (!trimmed || disabled) return;
        onSend(trimmed);
        setText('');
    };

    const handleKeyDown = (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="chat-input-area">
            <div className="chat-input-wrapper">
                <textarea
                    ref={textareaRef}
                    className="chat-input"
                    placeholder="Mô tả điểm đến, ngày đi, ngân sách..."
                    value={text}
                    onChange={(event) => setText(event.target.value)}
                    onKeyDown={handleKeyDown}
                    rows={3}
                    disabled={disabled}
                />
                <div className="composer-actions">
                    <div>
                        <button type="button" title="Đính kèm" disabled={disabled}>
                            <span className="material-symbols-outlined">attach_file</span>
                        </button>
                        <button type="button" title="Thêm địa điểm" disabled={disabled}>
                            <span className="material-symbols-outlined">location_on</span>
                        </button>
                    </div>
                    <button
                        className="send-btn"
                        type="button"
                        onClick={handleSend}
                        disabled={disabled || !text.trim()}
                        title="Gửi yêu cầu"
                    >
                        <span className="material-symbols-outlined">arrow_upward</span>
                    </button>
                </div>
            </div>
        </div>
    );
}
