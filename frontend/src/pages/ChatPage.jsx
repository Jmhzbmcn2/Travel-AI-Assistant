import { useCallback, useEffect, useState } from 'react';
import Sidebar from '../components/Sidebar';
import ChatPane from '../components/ChatPane';
import Workspace from '../components/Workspace';
import { Icon } from '../lib/ui';
import {
    deleteSession, executeTripAction, fetchSessionMessages, fetchSessions,
    fetchTrip, patchTripPlan, renameSession, sendMessage,
} from '../services/api';

const STATUS_PILL = {
    empty: { label: 'Nháp', color: 'var(--line-2)' },
    draft: { label: 'Bản nháp', color: 'var(--warn)' },
    decided: { label: 'Đã có kết quả', color: 'var(--ok)' },
};

export default function ChatPage() {
    const [messages, setMessages] = useState([]);
    const [sessions, setSessions] = useState([]);
    const [sessionId, setSessionId] = useState(null);
    const [isStreaming, setIsStreaming] = useState(false);
    const [streamContent, setStreamContent] = useState('');
    const [agentStatus, setAgentStatus] = useState('');
    const [workspace, setWorkspace] = useState(null);
    const [savingPlan, setSavingPlan] = useState(false);
    const [wsCollapsed, setWsCollapsed] = useState(false);
    const [loadingAction, setLoadingAction] = useState(null);
    const [workspaceError, setWorkspaceError] = useState('');
    const [isWorkspaceLoading, setIsWorkspaceLoading] = useState(false);
    const [actionDiff, setActionDiff] = useState('');
    const [wsTab, setWsTab] = useState('overview');
    const [editingPlan, setEditingPlan] = useState(false);

    const [theme, setTheme] = useState(() => {
        const q = new URLSearchParams(window.location.search).get('theme');
        if (q === 'dark' || q === 'light') return q;
        try { return localStorage.getItem('theme'); } catch { return null; }
    });
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [isNarrow, setIsNarrow] = useState(false);
    const [mobileTab, setMobileTab] = useState('chat');

    useEffect(() => {
        const root = document.documentElement;
        if (theme) root.dataset.theme = theme; else delete root.dataset.theme;
        try { theme ? localStorage.setItem('theme', theme) : localStorage.removeItem('theme'); } catch { /* ignore */ }
    }, [theme]);

    useEffect(() => {
        const mq = window.matchMedia('(max-width: 860px)');
        const on = (e) => setIsNarrow(e.matches);
        setIsNarrow(mq.matches);
        mq.addEventListener('change', on);
        return () => mq.removeEventListener('change', on);
    }, []);

    const loadSessions = useCallback(async () => setSessions(await fetchSessions()), []);

    const loadWorkspace = useCallback(async (sid) => {
        if (!sid) return;
        setIsWorkspaceLoading(true);
        setWorkspaceError('');
        try {
            setWorkspace(await fetchTrip(sid));
        } catch (e) {
            setWorkspaceError(`Không tải được workspace: ${e.message}`);
        } finally {
            setIsWorkspaceLoading(false);
        }
    }, []);

    useEffect(() => { loadSessions(); }, [loadSessions]);

    useEffect(() => {
        const sid = new URLSearchParams(window.location.search).get('session');
        if (sid) handleSelectSession(sid);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const resetConversation = () => {
        setSessionId(null);
        setMessages([]);
        setStreamContent('');
        setWorkspace(null);
        setWorkspaceError('');
        setActionDiff('');
        setMobileTab('chat');
        setWsTab('overview');
        setEditingPlan(false);
    };

    const handleSelectSession = async (sid) => {
        setSessionId(sid);
        setWorkspaceError('');
        setActionDiff('');
        setWsTab('overview');
        setEditingPlan(false);
        setMessages(await fetchSessionMessages(sid));
        loadWorkspace(sid);
    };

    const handleDeleteSession = async (sid) => {
        await deleteSession(sid);
        if (sessionId === sid) resetConversation();
        loadSessions();
    };

    const handleRenameSession = async (sid, title) => {
        try { await renameSession(sid, title); loadSessions(); }
        catch (e) { setWorkspaceError(`Lỗi đổi tên: ${e.message}`); }
    };

    const handleSend = async (text) => {
        setMessages((prev) => [...prev, { role: 'user', content: text }]);
        setIsStreaming(true);
        setStreamContent('');
        setAgentStatus('');
        setWorkspaceError('');
        setActionDiff('');
        if (isNarrow) setMobileTab('chat');

        let acc = '';
        await sendMessage(
            text, sessionId,
            (chunk) => { setAgentStatus(''); acc += chunk; setStreamContent(acc); },
            (newSid) => {
                if (acc) setMessages((prev) => [...prev, { role: 'assistant', content: acc }]);
                setStreamContent(''); setIsStreaming(false); setAgentStatus('');
                setSessionId(newSid);
                loadWorkspace(newSid);
                loadSessions();
            },
            (err) => {
                setMessages((prev) => [...prev, { role: 'assistant', content: `Lỗi: ${err}` }]);
                setStreamContent(''); setIsStreaming(false); setAgentStatus('');
            },
            () => {},
            (statusText) => setAgentStatus(statusText),
        );
    };

    const handleSavePlan = async (patch) => {
        setSavingPlan(true);
        setWorkspaceError('');
        try {
            setWorkspace(await patchTripPlan(sessionId, patch));
            setEditingPlan(false);
        } catch (e) {
            setWorkspaceError(`Lỗi cập nhật kế hoạch: ${e.message}`);
        } finally {
            setSavingPlan(false);
        }
    };

    const handleTripAction = async (action, targetDay, targetPlaceId) => {
        if (!sessionId) return;
        setLoadingAction({ action, target: targetDay || targetPlaceId });
        setWorkspaceError('');
        try {
            const res = await executeTripAction(sessionId, action, targetDay, targetPlaceId);
            if (res.status === 'success') {
                setActionDiff(res.message || 'Đã cập nhật lịch trình');
                setWsTab('itinerary');
                setMessages((prev) => [...prev, { role: 'assistant', content: res.message }]);
                await loadWorkspace(sessionId);
            } else {
                setWorkspaceError(res.message || 'Không thực hiện được');
            }
        } catch (e) {
            setWorkspaceError(`Lỗi: ${e.message}`);
        } finally {
            setLoadingAction(null);
        }
    };

    const showWorkspace = isNarrow ? mobileTab === 'workspace' : !wsCollapsed;
    const showChat = isNarrow ? mobileTab === 'chat' : true;
    const dest = workspace?.plan?.destination;
    const statusPill = workspace?.status ? STATUS_PILL[workspace.status] : null;

    return (
        <div style={{ height: '100%', background: 'var(--page)', color: 'var(--text)' }}>
            <Sidebar
                sessions={sessions}
                activeSession={sessionId}
                onSelectSession={handleSelectSession}
                onNewChat={resetConversation}
                onDeleteSession={handleDeleteSession}
                onRenameSession={handleRenameSession}
                open={sidebarOpen}
                onClose={() => setSidebarOpen(false)}
            />

            <div data-shell="1" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                {isNarrow && (
                    <div data-mobiletabs="1" style={{ display: 'flex', gap: 2, padding: '8px 14px', background: 'var(--soft)', borderBottom: '1px solid var(--line)' }}>
                        {[['chat', 'Trò chuyện'], ['workspace', 'Kế hoạch']].map(([id, label]) => (
                            <button key={id} type="button" onClick={() => setMobileTab(id)} style={{ flex: 1, padding: '8px 10px', borderRadius: 8, fontSize: 12.5, fontWeight: 600, background: mobileTab === id ? 'var(--pri)' : 'transparent', color: mobileTab === id ? 'var(--on-pri)' : 'var(--dim)' }}>
                                {label}
                            </button>
                        ))}
                    </div>
                )}

                <div style={{ flex: 1, minHeight: 0, display: 'flex' }}>
                    {showChat && (
                        <ChatPane
                            messages={messages}
                            streamContent={streamContent}
                            isStreaming={isStreaming}
                            agentStatus={agentStatus}
                            onSend={handleSend}
                            tripTitle={dest ? `Chuyến đi ${dest}` : null}
                            tripStatus={statusPill}
                            wsCollapsed={wsCollapsed}
                            onToggleWs={() => (isNarrow ? setMobileTab('workspace') : setWsCollapsed((v) => !v))}
                            onOpenSidebar={() => setSidebarOpen(true)}
                            onToggleTheme={() => setTheme((t) => (resolvedDark(t) ? 'light' : 'dark'))}
                            themeIcon={resolvedDark(theme) ? 'light_mode' : 'dark_mode'}
                        />
                    )}
                    {showWorkspace && (
                        <div style={{ flex: isNarrow ? '1 1 auto' : '0 0 528px', width: isNarrow ? '100%' : 528, minWidth: 0, borderLeft: isNarrow ? 'none' : '1px solid var(--line)' }}>
                            <Workspace
                                workspace={workspace}
                                sessionId={sessionId}
                                onSavePlan={handleSavePlan}
                                savingPlan={savingPlan}
                                onTripAction={handleTripAction}
                                loadingAction={loadingAction}
                                workspaceError={workspaceError}
                                isLoading={isWorkspaceLoading}
                                actionDiff={actionDiff}
                                onToggleCollapse={() => (isNarrow ? setMobileTab('chat') : setWsCollapsed(true))}
                                tab={wsTab}
                                onTab={setWsTab}
                                editing={editingPlan}
                                onEdit={() => setEditingPlan(true)}
                                onCancelEdit={() => setEditingPlan(false)}
                            />
                        </div>
                    )}
                    {!isNarrow && wsCollapsed && (
                        <button
                            type="button"
                            onClick={() => setWsCollapsed(false)}
                            title="Mở kế hoạch"
                            style={{ position: 'fixed', right: 0, top: '50%', transform: 'translateY(-50%)', display: 'grid', placeItems: 'center', width: 30, height: 60, borderRadius: '9px 0 0 9px', border: '1px solid var(--line)', borderRight: 0, background: 'var(--surface)', color: 'var(--dim)' }}
                        >
                            <Icon name="left_panel_open" size={18} />
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}

function resolvedDark(theme) {
    if (theme === 'dark') return true;
    if (theme === 'light') return false;
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
}
