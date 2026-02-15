import { useState, useEffect, useRef, useCallback } from 'react';
import ChatBubble from '../components/ChatBubble';
import ChatInput from '../components/ChatInput';
import TypingIndicator from '../components/TypingIndicator';
import Sidebar from '../components/Sidebar';
import { sendMessage, fetchSessions, fetchSessionMessages, deleteSession } from '../services/api';

const SUGGESTIONS = [
    { emoji: '🛫', text: 'Tìm vé máy bay Hà Nội → Đà Nẵng ngày 20/3' },
    { emoji: '🏖️', text: 'Bay từ Sài Gòn đi Phú Quốc cuối tuần này' },
    { emoji: '🏨', text: 'Vé rẻ HCM đi Nha Trang + khách sạn' },
    { emoji: '👨‍👩‍👧‍👦', text: 'Đặt vé Hà Nội → Đà Lạt cho 2 người' },
];

const FEATURES = [
    { icon: '🔍', label: 'Tìm vé rẻ' },
    { icon: '🏨', label: 'Đặt khách sạn' },
    { icon: '💰', label: 'So sánh giá' },
    { icon: '📊', label: 'Xếp hạng deal' },
];

export default function ChatPage() {
    const [messages, setMessages] = useState([]);
    const [sessions, setSessions] = useState([]);
    const [sessionId, setSessionId] = useState(null);
    const [isStreaming, setIsStreaming] = useState(false);
    const [streamContent, setStreamContent] = useState('');
    const messagesEndRef = useRef(null);

    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages, streamContent, scrollToBottom]);

    useEffect(() => {
        loadSessions();
    }, []);

    const loadSessions = async () => {
        const data = await fetchSessions();
        setSessions(data);
    };

    const handleSelectSession = async (sid) => {
        setSessionId(sid);
        const msgs = await fetchSessionMessages(sid);
        setMessages(msgs);
    };

    const handleNewChat = () => {
        setSessionId(null);
        setMessages([]);
    };

    const handleDeleteSession = async (sid) => {
        await deleteSession(sid);
        if (sessionId === sid) {
            setSessionId(null);
            setMessages([]);
        }
        loadSessions();
    };

    const handleSend = async (text) => {
        const userMsg = { role: 'user', content: text };
        setMessages((prev) => [...prev, userMsg]);
        setIsStreaming(true);
        setStreamContent('');

        let accumulatedContent = '';

        await sendMessage(
            text,
            sessionId,
            (chunk) => {
                accumulatedContent += chunk;
                setStreamContent(accumulatedContent);
            },
            (newSessionId) => {
                setMessages((prev) => [
                    ...prev,
                    { role: 'assistant', content: accumulatedContent },
                ]);
                setStreamContent('');
                setIsStreaming(false);
                setSessionId(newSessionId);
                loadSessions();
            },
            (err) => {
                setMessages((prev) => [
                    ...prev,
                    { role: 'assistant', content: `❌ Lỗi: ${err}` },
                ]);
                setStreamContent('');
                setIsStreaming(false);
            }
        );
    };

    const showWelcome = messages.length === 0 && !isStreaming;

    return (
        <div className="app-layout">
            <Sidebar
                sessions={sessions}
                activeSession={sessionId}
                onSelectSession={handleSelectSession}
                onNewChat={handleNewChat}
                onDeleteSession={handleDeleteSession}
            />

            <main className="chat-area">
                {/* Header */}
                <div className="chat-header">
                    <div className="chat-header-icon">✈️</div>
                    <div className="chat-header-info">
                        <h2>Travel AI Assistant</h2>
                        <span>Tìm vé máy bay & khách sạn giá tốt nhất</span>
                    </div>
                    <span className="chat-header-badge">⚡ Gemini</span>
                </div>

                {/* Messages */}
                <div className="messages-container">
                    {showWelcome ? (
                        <div className="welcome-screen">
                            <div className="welcome-icon-wrapper">
                                <div className="welcome-icon">🌏</div>
                            </div>
                            <h1 className="welcome-title">Xin chào! Bạn muốn đi đâu?</h1>
                            <p className="welcome-sub">
                                Tôi giúp bạn tìm vé máy bay giá rẻ, khách sạn tốt nhất
                                và so sánh các deal hấp dẫn nhất cho chuyến đi.
                            </p>

                            <div className="welcome-features">
                                {FEATURES.map((f, i) => (
                                    <div key={i} className="feature-item">
                                        <span className="feature-icon">{f.icon}</span>
                                        {f.label}
                                    </div>
                                ))}
                            </div>

                            <div className="welcome-suggestions">
                                {SUGGESTIONS.map((s, i) => (
                                    <button
                                        key={i}
                                        className="suggestion-chip"
                                        onClick={() => handleSend(s.text)}
                                    >
                                        <span className="suggestion-emoji">{s.emoji}</span>
                                        <span className="suggestion-text">{s.text}</span>
                                    </button>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <>
                            {messages.map((msg, i) => (
                                <ChatBubble key={i} role={msg.role} content={msg.content} />
                            ))}
                            {isStreaming && streamContent && (
                                <ChatBubble role="assistant" content={streamContent} />
                            )}
                            {isStreaming && !streamContent && <TypingIndicator />}
                        </>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input */}
                <ChatInput onSend={handleSend} disabled={isStreaming} />
            </main>
        </div>
    );
}
