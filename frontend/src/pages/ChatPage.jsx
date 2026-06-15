import { useCallback, useEffect, useRef, useState } from 'react';
import ChatBubble, { InterruptBubble } from '../components/ChatBubble';
import ChatInput from '../components/ChatInput';
import Sidebar from '../components/Sidebar';
import TripWorkspace from '../components/TripWorkspace';
import TypingIndicator from '../components/TypingIndicator';
import { deleteSession, renameSession, fetchSessionMessages, fetchSessions, fetchTrip, patchTripPlan, resumeChat, sendMessage, executeTripAction } from '../services/api';

export default function ChatPage() {
    const [messages, setMessages] = useState([]);
    const [sessions, setSessions] = useState([]);
    const [sessionId, setSessionId] = useState(null);
    const [isStreaming, setIsStreaming] = useState(false);
    const [streamContent, setStreamContent] = useState('');
    const [interruptData, setInterruptData] = useState(null);
    const [isResuming, setIsResuming] = useState(false);
    const [workspace, setWorkspace] = useState(null);
    const [editingPlan, setEditingPlan] = useState(false);
    const [savingPlan, setSavingPlan] = useState(false);
    const [isWorkspaceCollapsed, setIsWorkspaceCollapsed] = useState(false);
    const [agentStatus, setAgentStatus] = useState('');
    const [loadingAction, setLoadingAction] = useState(null);
    const messagesEndRef = useRef(null);

    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, []);

    const loadSessions = useCallback(async () => {
        const data = await fetchSessions();
        setSessions(data);
    }, []);

    const loadWorkspace = useCallback(async (sid) => {
        setWorkspace(await fetchTrip(sid));
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages, streamContent, interruptData, scrollToBottom]);

    useEffect(() => {
        const timer = window.setTimeout(() => {
            loadSessions();
        }, 0);
        return () => window.clearTimeout(timer);
    }, [loadSessions]);

    const handleSelectSession = async (sid) => {
        setSessionId(sid);
        setInterruptData(null);
        const msgs = await fetchSessionMessages(sid);
        setMessages(msgs);
        loadWorkspace(sid);
    };

    const handleNewChat = () => {
        setSessionId(null);
        setMessages([]);
        setInterruptData(null);
        setStreamContent('');
        setWorkspace(null);
        setEditingPlan(false);
    };

    const handleDeleteSession = async (sid) => {
        await deleteSession(sid);
        if (sessionId === sid) {
            setSessionId(null);
            setMessages([]);
            setInterruptData(null);
            setStreamContent('');
        }
        loadSessions();
    };

    const handleRenameSession = async (sid, title) => {
        try {
            await renameSession(sid, title);
            loadSessions();
        } catch (error) {
            setMessages((prev) => [...prev, { role: 'assistant', content: `Lỗi đổi tên cuộc hội thoại: ${error.message}` }]);
        }
    };

    const handleSend = async (text) => {
        const userMsg = { role: 'user', content: text };
        setMessages((prev) => [...prev, userMsg]);
        setIsStreaming(true);
        setStreamContent('');
        setInterruptData(null);
        setAgentStatus('');

        let accumulatedContent = '';

        await sendMessage(
            text,
            sessionId,
            (chunk) => {
                setAgentStatus('');
                accumulatedContent += chunk;
                setStreamContent(accumulatedContent);
            },
            (newSessionId) => {
                if (accumulatedContent) {
                    setMessages((prev) => [...prev, { role: 'assistant', content: accumulatedContent }]);
                }
                setStreamContent('');
                setIsStreaming(false);
                setAgentStatus('');
                setSessionId(newSessionId);
                loadWorkspace(newSessionId);
                loadSessions();
            },
            (err) => {
                setMessages((prev) => [...prev, { role: 'assistant', content: `Lỗi: ${err}` }]);
                setStreamContent('');
                setIsStreaming(false);
                setAgentStatus('');
            },
            (data, newSessionId) => {
                setIsStreaming(false);
                setStreamContent('');
                setAgentStatus('');
                setSessionId(newSessionId);
                setInterruptData(data);
                loadWorkspace(newSessionId);
                loadSessions();
            },
            (statusText) => {
                setAgentStatus(statusText);
            }
        );
    };

    const handleConfirm = async (response) => {
        if ((!interruptData && workspace?.status !== 'awaiting_confirmation') || isResuming) return;

        setIsResuming(true);
        setInterruptData(null);
        setIsStreaming(true);
        setStreamContent('');
        setAgentStatus('');

        const confirmText = typeof response === 'string' ? response : 'Đã xác nhận';
        setMessages((prev) => [
            ...prev,
            { role: 'assistant', content: interruptData?.content || 'Kế hoạch đã lưu và đang chờ xác nhận.' },
            { role: 'user', content: confirmText === 'ok' ? 'Xác nhận' : confirmText },
        ]);

        let accumulatedContent = '';

        await resumeChat(
            sessionId,
            response,
            (chunk) => {
                setAgentStatus('');
                accumulatedContent += chunk;
                setStreamContent(accumulatedContent);
            },
            () => {
                if (accumulatedContent) {
                    setMessages((prev) => [...prev, { role: 'assistant', content: accumulatedContent }]);
                }
                setStreamContent('');
                setIsStreaming(false);
                setIsResuming(false);
                setAgentStatus('');
                loadWorkspace(sessionId);
                loadSessions();
            },
            (err) => {
                setMessages((prev) => [...prev, { role: 'assistant', content: `Lỗi: ${err}` }]);
                setStreamContent('');
                setIsStreaming(false);
                setIsResuming(false);
                setAgentStatus('');
            },
            (data) => {
                setIsStreaming(false);
                setStreamContent('');
                setIsResuming(false);
                setInterruptData(data);
                setAgentStatus('');
            },
            (statusText) => {
                setAgentStatus(statusText);
            }
        );
    };

    const handleModify = () => {
        if (!workspace?.plan) return;
        setEditingPlan(true);
    };

    const handleSavePlan = async (patch) => {
        setSavingPlan(true);
        try {
            const updated = await patchTripPlan(sessionId, patch);
            setWorkspace(updated);
            setEditingPlan(false);
        } catch (error) {
            setMessages((prev) => [...prev, { role: 'assistant', content: `Lỗi cập nhật kế hoạch: ${error.message}` }]);
        } finally {
            setSavingPlan(false);
        }
    };

    const handleTripAction = async (action, targetDay, targetPlaceId) => {
        if (!sessionId) return;
        setLoadingAction({ action, target: targetDay || targetPlaceId });
        try {
            const res = await executeTripAction(sessionId, action, targetDay, targetPlaceId);
            if (res.status === 'success') {
                setMessages(prev => [
                    ...prev,
                    { role: 'assistant', content: res.message }
                ]);
                await loadWorkspace(sessionId);
            } else {
                setMessages(prev => [
                    ...prev,
                    { role: 'assistant', content: `Không thể thực hiện: ${res.message}` }
                ]);
            }
        } catch (error) {
            setMessages(prev => [
                ...prev,
                { role: 'assistant', content: `Lỗi: ${error.message}` }
            ]);
        } finally {
            setLoadingAction(null);
        }
    };

    const showWelcome = messages.length === 0 && !isStreaming && !interruptData;

    return (
        <div className="app-layout">
            <Sidebar
                sessions={sessions}
                activeSession={sessionId}
                onSelectSession={handleSelectSession}
                onNewChat={handleNewChat}
                onDeleteSession={handleDeleteSession}
                onRenameSession={handleRenameSession}
            />

            <main className="main-shell">
                <section className="command-panel" aria-label="Lập kế hoạch chuyến đi">
                    <header className="command-header">
                        <h2>Lập kế hoạch chuyến đi</h2>
                        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                            <button
                                className="header-menu"
                                type="button"
                                title={isWorkspaceCollapsed ? "Mở Workspace" : "Thu gọn Workspace"}
                                onClick={() => setIsWorkspaceCollapsed(!isWorkspaceCollapsed)}
                            >
                                <span className="material-symbols-outlined">
                                    {isWorkspaceCollapsed ? "chrome_reader_mode" : "right_panel_close"}
                                </span>
                            </button>
                            <button className="header-menu" type="button" title="Tùy chọn">
                                <span className="material-symbols-outlined">more_vert</span>
                            </button>
                        </div>
                    </header>

                    <div className="messages-container">
                        {showWelcome ? (
                            <div className="welcome-screen">
                                <span className="welcome-kicker">Travel planner</span>
                                <h1 className="welcome-title">Biến ý tưởng du lịch thành kế hoạch có thể đi</h1>
                                <p className="welcome-sub">
                                    Nhập điểm đến, ngày đi, ngân sách và sở thích. Workspace bên phải sẽ giúp kiểm tra
                                    lịch trình, chi phí, rủi ro và bước tiếp theo.
                                </p>
                                <div className="welcome-suggestions">
                                    <button type="button" onClick={() => handleSend('Lập lịch trình đi Đà Nẵng 4 ngày 3 đêm cho 2 người lớn, ngân sách khoảng 10 triệu. Thích đi dạo, ăn uống, không đi quá mệt.')}>
                                        Đà Nẵng 4N3Đ, 2 người, 10 triệu
                                    </button>
                                    <button type="button" onClick={() => handleSend('Tôi muốn đi Phú Quốc 3 ngày 2 đêm, ưu tiên biển và đồ ăn ngon.')}>
                                        Phú Quốc 3N2Đ, biển và ăn uống
                                    </button>
                                    <button type="button" onClick={() => handleSend('Gợi ý chuyến đi Thái Lan 5 ngày cho nhóm bạn, cần tối ưu chi phí.')}>
                                        Thái Lan 5 ngày, tối ưu chi phí
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <>
                                {messages.map((msg, i) => (
                                    <ChatBubble key={`${msg.role}-${i}`} role={msg.role} content={msg.content} />
                                ))}

                                {interruptData && (
                                    <InterruptBubble
                                        message={interruptData.content || 'Bạn có muốn xác nhận kế hoạch này không?'}
                                        onConfirm={handleConfirm}
                                        onModify={handleModify}
                                        disabled={isResuming || Boolean(workspace?.missing_fields?.length)}
                                    />
                                )}

                                {isStreaming && streamContent && <ChatBubble role="assistant" content={streamContent} />}
                                {isStreaming && !streamContent && <TypingIndicator status={agentStatus} />}
                            </>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    <ChatInput onSend={handleSend} disabled={isStreaming || Boolean(interruptData)} />
                </section>

                <TripWorkspace
                    workspace={workspace}
                    sessionId={sessionId}
                    onConfirm={handleConfirm}
                    editing={editingPlan}
                    onEdit={handleModify}
                    onSavePlan={handleSavePlan}
                    onCancelEdit={() => setEditingPlan(false)}
                    savingPlan={savingPlan}
                    isCollapsed={isWorkspaceCollapsed}
                    onToggleCollapse={() => setIsWorkspaceCollapsed(!isWorkspaceCollapsed)}
                    onTripAction={handleTripAction}
                    loadingAction={loadingAction}
                />
            </main>
        </div>
    );
}
