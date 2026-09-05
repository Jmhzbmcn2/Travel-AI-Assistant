import { useEffect, useState } from 'react';
import { Icon } from '../lib/ui';

export default function Sidebar({
    sessions,
    activeSession,
    onSelectSession,
    onNewChat,
    onDeleteSession,
    onRenameSession,
    open,
    onClose,
}) {
    const [menuFor, setMenuFor] = useState(null);
    const [editingId, setEditingId] = useState(null);
    const [renameText, setRenameText] = useState('');
    const [query, setQuery] = useState('');

    useEffect(() => {
        const close = () => setMenuFor(null);
        document.addEventListener('click', close);
        return () => document.removeEventListener('click', close);
    }, []);

    const saveRename = (sid) => {
        const next = renameText.trim();
        const current = sessions.find((s) => s.session_id === sid)?.title;
        if (next && next !== current) onRenameSession(sid, next);
        setEditingId(null);
    };

    const filtered = query
        ? sessions.filter((s) => (s.title || '').toLowerCase().includes(query.toLowerCase()))
        : sessions;

    return (
        <>
            {open && (
                <div
                    data-scrim="1"
                    onClick={onClose}
                    style={{ position: 'fixed', inset: 0, zIndex: 44, background: 'rgba(15,20,19,.4)' }}
                />
            )}
            <aside
                data-sidebar="1"
                style={{
                    position: 'fixed', top: 0, bottom: 0, left: 0, zIndex: 45, width: 268,
                    transform: open ? 'translateX(0)' : 'translateX(-100%)',
                    transition: 'transform .22s ease',
                    display: 'flex', flexDirection: 'column', gap: 16, padding: '16px 14px',
                    background: 'var(--soft)', borderRight: '1px solid var(--line)',
                    boxShadow: open ? '2px 0 22px rgb(0 0 0 / .14)' : 'none',
                }}
            >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, padding: '2px 4px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
                        <div style={{ width: 32, height: 32, flex: '0 0 32px', display: 'grid', placeItems: 'center', borderRadius: 10, background: 'var(--pri)', color: 'var(--on-pri)' }}>
                            <Icon name="explore" size={19} />
                        </div>
                        <div style={{ minWidth: 0 }}>
                            <div style={{ fontSize: 14, fontWeight: 700, letterSpacing: '-.01em' }}>Lộ trình</div>
                            <div style={{ fontSize: 11, fontWeight: 500, color: 'var(--subtle)' }}>Trợ lý ra quyết định</div>
                        </div>
                    </div>
                    <button type="button" onClick={onClose} title="Đóng" style={btnIcon}>
                        <Icon name="close" size={18} />
                    </button>
                </div>

                <button
                    type="button"
                    onClick={() => { onNewChat(); onClose(); }}
                    style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 7, minHeight: 40, borderRadius: 10, background: 'var(--pri)', color: 'var(--on-pri)', fontSize: 13, fontWeight: 600 }}
                >
                    <Icon name="add" size={18} />Chuyến đi mới
                </button>

                <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '0 10px', minHeight: 36, border: '1px solid var(--line)', borderRadius: 9, background: 'var(--surface)' }}>
                    <Icon name="search" size={16} color="var(--subtle)" />
                    <input
                        type="text"
                        placeholder="Tìm chuyến đi"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        style={{ flex: 1, minWidth: 0, border: 0, outline: 0, background: 'transparent', fontSize: 12.5 }}
                    />
                </div>

                <nav style={{ flex: 1, minHeight: 0, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 14 }}>
                    <div>
                        <div style={groupLabel}>Gần đây</div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                            {filtered.length === 0 && (
                                <div style={{ padding: '8px 10px', fontSize: 12, color: 'var(--subtle)' }}>
                                    {query ? 'Không có kết quả' : 'Chưa có chuyến đi nào'}
                                </div>
                            )}
                            {filtered.map((s) => {
                                const active = s.session_id === activeSession;
                                if (editingId === s.session_id) {
                                    return (
                                        <input
                                            key={s.session_id}
                                            autoFocus
                                            value={renameText}
                                            onChange={(e) => setRenameText(e.target.value)}
                                            onBlur={() => saveRename(s.session_id)}
                                            onKeyDown={(e) => {
                                                if (e.key === 'Enter') saveRename(s.session_id);
                                                if (e.key === 'Escape') setEditingId(null);
                                            }}
                                            style={{ padding: '8px 10px', border: '1px solid var(--pri-line)', borderRadius: 9, background: 'var(--surface)', fontSize: 12.5, outline: 0 }}
                                        />
                                    );
                                }
                                return (
                                    <div key={s.session_id} style={{ position: 'relative', display: 'flex', alignItems: 'center', gap: 9, padding: '8px 10px', borderRadius: 9, background: active ? 'var(--muted)' : 'transparent' }}>
                                        <span style={{ width: 7, height: 7, flex: '0 0 7px', borderRadius: '50%', background: active ? 'var(--pri)' : 'var(--line-2)' }} />
                                        <button
                                            type="button"
                                            onClick={() => { onSelectSession(s.session_id); onClose(); }}
                                            style={{ flex: 1, minWidth: 0, textAlign: 'left', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 12.5, fontWeight: active ? 600 : 500, color: active ? 'var(--text)' : 'var(--dim)' }}
                                        >
                                            {s.title || 'Chuyến đi'}
                                        </button>
                                        <button type="button" onClick={(e) => { e.stopPropagation(); setMenuFor(menuFor === s.session_id ? null : s.session_id); }} style={{ display: 'grid', placeItems: 'center', color: 'var(--subtle)' }}>
                                            <Icon name="more_horiz" size={16} />
                                        </button>
                                        {menuFor === s.session_id && (
                                            <div style={{ position: 'absolute', top: '100%', right: 6, zIndex: 5, minWidth: 130, padding: 4, border: '1px solid var(--line)', borderRadius: 9, background: 'var(--surface)', boxShadow: '0 8px 24px rgb(0 0 0 / .12)' }}>
                                                <button type="button" onClick={(e) => { e.stopPropagation(); setEditingId(s.session_id); setRenameText(s.title || ''); setMenuFor(null); }} style={menuItem}>Đổi tên</button>
                                                <button type="button" onClick={(e) => { e.stopPropagation(); onDeleteSession(s.session_id); setMenuFor(null); }} style={{ ...menuItem, color: 'var(--dgr)' }}>Xoá</button>
                                            </div>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </nav>

                <div style={{ display: 'flex', alignItems: 'center', gap: 9, padding: '8px 10px', borderTop: '1px solid var(--line)' }}>
                    <div style={{ width: 26, height: 26, flex: '0 0 26px', display: 'grid', placeItems: 'center', borderRadius: 8, background: 'var(--muted)', fontSize: 11, fontWeight: 700, color: 'var(--dim)' }}>L</div>
                    <div style={{ flex: 1, minWidth: 0, fontSize: 12, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>Bản demo</div>
                </div>
            </aside>
        </>
    );
}

const btnIcon = { display: 'grid', placeItems: 'center', width: 28, height: 28, flex: '0 0 28px', borderRadius: 8, color: 'var(--subtle)' };
const groupLabel = { padding: '0 8px 6px', fontSize: 10.5, fontWeight: 600, letterSpacing: '.08em', textTransform: 'uppercase', color: 'var(--subtle)' };
const menuItem = { display: 'block', width: '100%', textAlign: 'left', padding: '7px 9px', borderRadius: 6, fontSize: 12.5, fontWeight: 500 };
