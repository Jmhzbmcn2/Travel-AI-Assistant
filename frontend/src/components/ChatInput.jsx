import { useState, useRef, useEffect } from 'react';

export default function ChatInput({ onSend, disabled }) {
    const [text, setText] = useState('');
    const textareaRef = useRef(null);

    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
        }
    }, [text]);

    const handleSend = () => {
        const trimmed = text.trim();
        if (!trimmed || disabled) return;
        onSend(trimmed);
        setText('');
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="chat-input-area">
            <div className="chat-input-wrapper">
                <textarea
                    ref={textareaRef}
                    className="chat-input"
                    placeholder="Hỏi tôi về chuyến du lịch của bạn..."
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    onKeyDown={handleKeyDown}
                    rows={1}
                    disabled={disabled}
                />
                <button
                    className="send-btn"
                    onClick={handleSend}
                    disabled={disabled || !text.trim()}
                    title="Gửi"
                >
                    ↗
                </button>
            </div>
            <div className="input-hint">Enter để gửi · Shift + Enter để xuống dòng</div>
        </div>
    );
}
