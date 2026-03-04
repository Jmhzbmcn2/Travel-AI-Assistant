import { useState, useEffect, useRef, useCallback } from 'react';
import ChatBubble, { InterruptBubble } from '../components/ChatBubble';
import ChatInput from '../components/ChatInput';
import TypingIndicator from '../components/TypingIndicator';
import Sidebar from '../components/Sidebar';
import { sendMessage, resumeChat, fetchSessions, fetchSessionMessages, deleteSession } from '../services/api';

export default function ChatPage() {
    const [messages, setMessages] = useState([]);
    const [sessions, setSessions] = useState([]);
    const [sessionId, setSessionId] = useState(null);
    const [isStreaming, setIsStreaming] = useState(false);
    const [streamContent, setStreamContent] = useState('');
    const [interruptData, setInterruptData] = useState(null);
    const [isResuming, setIsResuming] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages, streamContent, interruptData, scrollToBottom]);

    useEffect(() => {
        loadSessions();
    }, []);

    const loadSessions = async () => {
        const data = await fetchSessions();
        setSessions(data);
    };

    const handleSelectSession = async (sid) => {
        setSessionId(sid);
        setInterruptData(null);
        const msgs = await fetchSessionMessages(sid);
        setMessages(msgs);
    };

    const handleNewChat = () => {
        setSessionId(null);
        setMessages([]);
        setInterruptData(null);
    };

    const handleDeleteSession = async (sid) => {
        await deleteSession(sid);
        if (sessionId === sid) {
            setSessionId(null);
            setMessages([]);
            setInterruptData(null);
        }
        loadSessions();
    };

    const handleSend = async (text) => {
        const userMsg = { role: 'user', content: text };
        setMessages((prev) => [...prev, userMsg]);
        setIsStreaming(true);
        setStreamContent('');
        setInterruptData(null);

        let accumulatedContent = '';

        await sendMessage(
            text,
            sessionId,
            (chunk) => {
                accumulatedContent += chunk;
                setStreamContent(accumulatedContent);
            },
            (newSessionId) => {
                if (accumulatedContent) {
                    setMessages((prev) => [
                        ...prev,
                        { role: 'assistant', content: accumulatedContent },
                    ]);
                }
                setStreamContent('');
                setIsStreaming(false);
                setSessionId(newSessionId);
                loadSessions();
            },
            (err) => {
                setMessages((prev) => [
                    ...prev,
                    { role: 'assistant', content: `Lỗi: ${err}` },
                ]);
                setStreamContent('');
                setIsStreaming(false);
            },
            (data, newSessionId) => {
                setIsStreaming(false);
                setStreamContent('');
                setSessionId(newSessionId);
                setInterruptData(data);
                loadSessions();
            }
        );
    };

    const handleConfirm = async (response) => {
        setIsResuming(true);
        setInterruptData(null);
        setIsStreaming(true);
        setStreamContent('');

        const confirmText = typeof response === 'string' ? response : 'Đã xác nhận';
        setMessages((prev) => [
            ...prev,
            { role: 'assistant', content: interruptData?.content || '' },
            { role: 'user', content: confirmText === 'ok' ? '✓ Xác nhận' : confirmText },
        ]);

        let accumulatedContent = '';

        await resumeChat(
            sessionId,
            response,
            (chunk) => {
                accumulatedContent += chunk;
                setStreamContent(accumulatedContent);
            },
            (sid) => {
                if (accumulatedContent) {
                    setMessages((prev) => [
                        ...prev,
                        { role: 'assistant', content: accumulatedContent },
                    ]);
                }
                setStreamContent('');
                setIsStreaming(false);
                setIsResuming(false);
                loadSessions();
            },
            (err) => {
                setMessages((prev) => [
                    ...prev,
                    { role: 'assistant', content: `Lỗi: ${err}` },
                ]);
                setStreamContent('');
                setIsStreaming(false);
                setIsResuming(false);
            },
            (data, sid) => {
                setIsStreaming(false);
                setStreamContent('');
                setIsResuming(false);
                setInterruptData(data);
            }
        );
    };

    const handleModify = () => {
        // Abandon interrupted graph → new session, let user retype
        const planMessage = interruptData?.content || '';
        setInterruptData(null);
        setSessionId(null); // new session → graph starts fresh
        setMessages((prev) => [
            ...prev,
            { role: 'assistant', content: planMessage + '\n\n✎ *Kế hoạch đã bị hủy. Hãy nhập yêu cầu mới hoặc sửa lại yêu cầu trước.*' },
        ]);
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
                    <div className="chat-header-info">
                        <h2>Travel AI Assistant</h2>
                        <span>Trợ lý du lịch thông minh</span>
                    </div>
                </div>

                {/* Messages */}
                <div className="messages-container">
                    {showWelcome ? (
                        <div className="welcome-screen">
                            <h1 className="welcome-title">Chào bạn, tôi có thể giúp gì?</h1>
                            <p className="welcome-sub">
                                Hãy nhập câu hỏi hoặc yêu cầu của bạn để bắt đầu.
                            </p>
                        </div>
                    ) : (
                        <>
                            {messages.map((msg, i) => (
                                <ChatBubble key={i} role={msg.role} content={msg.content} />
                            ))}

                            {interruptData && (
                                <InterruptBubble
                                    message={interruptData.content || 'Xác nhận?'}
                                    onConfirm={handleConfirm}
                                    onModify={handleModify}
                                    disabled={isResuming}
                                />
                            )}

                            {isStreaming && streamContent && (
                                <ChatBubble role="assistant" content={streamContent} />
                            )}
                            {isStreaming && !streamContent && <TypingIndicator />}
                        </>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input */}
                <ChatInput onSend={handleSend} disabled={isStreaming || !!interruptData} />
            </main>
        </div>
    );
}
