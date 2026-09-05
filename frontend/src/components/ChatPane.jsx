import { useEffect, useRef, useState } from 'react';
import { Icon } from '../lib/ui';
import { formatMarkdown } from '../lib/format';

const SUGGESTIONS = [
    { icon: 'beach_access', title: 'Đà Nẵng 4N3Đ, 2 người, 10 triệu', sub: 'Kiểm tra ngân sách · so 3 phương án', prompt: 'Lập lịch trình đi Đà Nẵng 4 ngày 3 đêm cho 2 người lớn từ Hà Nội, ngân sách khoảng 10 triệu. Thích đi dạo, ăn uống, không đi quá mệt.' },
    { icon: 'restaurant', title: 'Phú Quốc 3N2Đ, biển và ăn uống', sub: 'Lịch trình nhẹ · không di chuyển nhiều', prompt: 'Tôi muốn đi Phú Quốc 3 ngày 2 đêm từ TP HCM, ngân sách 8 triệu 1 người, ưu tiên biển và đồ ăn ngon, mức cân bằng.' },
    { icon: 'savings', title: 'Nha Trang 4 ngày, tối ưu chi phí', sub: 'Ưu tiên rẻ nhất · cảnh báo rủi ro', prompt: 'Gợi ý chuyến đi Nha Trang 4 ngày từ Hà Nội cho 2 người, ngân sách 12 triệu, cần tối ưu chi phí, thích biển.' },
];

const VALUE_TILES = [
    { icon: 'verified', title: 'Nói rõ độ tin cậy', sub: 'Từng con số ghi rõ đã xác minh hay còn là ước tính.' },
    { icon: 'rule', title: 'Bắt lỗi lịch trình', sub: 'Ngày quá dày, chặng quá xa, giờ bay quá sớm.' },
    { icon: 'compare_arrows', title: 'So phương án', sub: 'Tiết kiệm · Cân bằng · Thoải mái, kèm đánh đổi.' },
];

function Bubble({ role, content }) {
    if (role === 'user') {
        return (
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <div style={{ maxWidth: '80%', padding: '11px 14px', borderRadius: '14px 4px 14px 14px', background: 'var(--muted)', fontSize: 14, lineHeight: 1.55 }}>
                    {content}
                </div>
            </div>
        );
    }
    return (
        <div style={{ display: 'flex', gap: 11 }}>
            <div style={{ width: 28, height: 28, flex: '0 0 28px', display: 'grid', placeItems: 'center', borderRadius: 9, background: 'var(--pri-soft)', color: 'var(--pri)' }}>
                <Icon name="auto_awesome" size={17} />
            </div>
            <div
                className="md"
                style={{ minWidth: 0, padding: '12px 15px', border: '1px solid var(--line)', borderRadius: '4px 14px 14px 14px', background: 'var(--soft)' }}
                dangerouslySetInnerHTML={{ __html: formatMarkdown(content) }}
            />
        </div>
    );
}

function ProcessingCard({ status }) {
    return (
        <div style={{ display: 'flex', gap: 11 }}>
            <div style={{ width: 28, height: 28, flex: '0 0 28px', display: 'grid', placeItems: 'center', borderRadius: 9, background: 'var(--pri-soft)', color: 'var(--pri)' }}>
                <Icon name="auto_awesome" size={17} />
            </div>
            <div style={{ minWidth: 0, flex: 1, maxWidth: 420, padding: '13px 15px', border: '1px solid var(--line)', borderRadius: '4px 14px 14px 14px', background: 'var(--soft)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 9, fontSize: 12.5, fontWeight: 600, marginBottom: 11 }}>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--pri)', animation: 'pulseDot 1.1s ease-in-out infinite' }} />
                    {status || 'Đội trợ lý đang làm việc…'}
                </div>
                <div style={{ height: 3, borderRadius: 999, background: 'var(--muted)', overflow: 'hidden' }}>
                    <div style={{ width: '38%', height: '100%', borderRadius: 999, background: 'var(--pri)', animation: 'sweep 1.3s ease-in-out infinite' }} />
                </div>
            </div>
        </div>
    );
}

export default function ChatPane({
    messages, streamContent, isStreaming, agentStatus, onSend,
    tripTitle, tripStatus, wsCollapsed, onToggleWs, onOpenSidebar, onToggleTheme, themeIcon,
}) {
    const [text, setText] = useState('');
    const taRef = useRef(null);
    const endRef = useRef(null);

    useEffect(() => {
        if (!taRef.current) return;
        taRef.current.style.height = 'auto';
        taRef.current.style.height = `${Math.min(Math.max(taRef.current.scrollHeight, 62), 150)}px`;
    }, [text]);

    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, streamContent, agentStatus]);

    const send = () => {
        const t = text.trim();
        if (!t || isStreaming) return;
        onSend(t);
        setText('');
    };

    const isWelcome = messages.length === 0 && !isStreaming;

    return (
        <section data-chat="1" style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', background: 'var(--surface)', borderRight: '1px solid var(--line)', overflow: 'hidden' }}>
            <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, minHeight: 56, padding: '10px 14px', borderBottom: '1px solid var(--line)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
                    <button type="button" onClick={onOpenSidebar} title="Menu" style={{ display: 'grid', placeItems: 'center', width: 32, height: 32, flex: '0 0 32px', borderRadius: 8, color: 'var(--dim)' }}>
                        <Icon name="menu" size={19} />
                    </button>
                    <span style={{ fontSize: 14, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', minWidth: 0 }}>
                        {tripTitle || 'Chuyến đi mới'}
                    </span>
                    {tripStatus && (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '3px 9px', borderRadius: 999, background: 'var(--muted)', fontSize: 11, fontWeight: 600, color: 'var(--dim)', flexShrink: 0 }}>
                            <span style={{ width: 6, height: 6, borderRadius: '50%', background: tripStatus.color }} />{tripStatus.label}
                        </span>
                    )}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4, flex: '0 0 auto' }}>
                    <button type="button" onClick={onToggleTheme} title="Đổi giao diện" style={hdrBtn}>
                        <Icon name={themeIcon} size={17} />
                    </button>
                    <button type="button" onClick={onToggleWs} title={wsCollapsed ? 'Mở kế hoạch' : 'Thu gọn kế hoạch'} style={hdrBtn}>
                        <Icon name={wsCollapsed ? 'right_panel_open' : 'right_panel_close'} size={18} />
                    </button>
                </div>
            </header>

            <div style={{ flex: 1, minHeight: 0, overflowY: 'auto', overflowX: 'hidden', padding: '18px 16px', scrollbarGutter: 'stable' }}>
                {isWelcome ? (
                    <div style={{ width: '100%', maxWidth: 620, margin: '0 auto', display: 'flex', flexDirection: 'column', justifyContent: 'center', minHeight: '100%', gap: 15 }}>
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7, alignSelf: 'flex-start', padding: '5px 11px', border: '1px solid var(--pri-line)', borderRadius: 999, background: 'var(--pri-soft)', fontSize: 11, fontWeight: 600, letterSpacing: '.04em', textTransform: 'uppercase', color: 'var(--pri)' }}>
                            <Icon name="bolt" size={14} />Công cụ ra quyết định
                        </span>
                        <h1 style={{ fontSize: 'clamp(20px, 5vw, 33px)', lineHeight: 1.16, fontWeight: 700, letterSpacing: '-.02em', overflowWrap: 'anywhere', maxWidth: '100%' }}>
                            Bạn đã có ý tưởng. Đây là câu trả lời <span style={{ color: 'var(--pri)' }}>đi được hay không</span>.
                        </h1>
                        <p style={{ maxWidth: '100%', fontSize: 'clamp(13.5px, 3.6vw, 15px)', lineHeight: 1.6, color: 'var(--dim)' }}>
                            Nhập điểm đi, điểm đến, ngày đi và ngân sách. Workspace sẽ kiểm tra lịch trình có hợp lý, chi phí có vừa túi, rủi ro nằm ở đâu — và nói rõ nên cắt gì.
                        </p>
                        <div style={{ display: 'grid', gap: 8, marginTop: 6 }}>
                            {SUGGESTIONS.map((s) => (
                                <button key={s.title} type="button" onClick={() => onSend(s.prompt)} style={{ display: 'flex', alignItems: 'center', gap: 13, padding: '14px 15px', border: '1px solid var(--line)', borderRadius: 12, background: 'var(--soft)', textAlign: 'left' }}>
                                    <Icon name={s.icon} size={20} color="var(--pri)" />
                                    <span style={{ flex: 1, minWidth: 0 }}>
                                        <span style={{ display: 'block', fontSize: 14, fontWeight: 600 }}>{s.title}</span>
                                        <span style={{ display: 'block', marginTop: 2, fontSize: 12, color: 'var(--subtle)' }}>{s.sub}</span>
                                    </span>
                                    <Icon name="arrow_forward" size={18} color="var(--subtle)" />
                                </button>
                            ))}
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,minmax(0,1fr))', gap: 10, marginTop: 14, paddingTop: 18, borderTop: '1px solid var(--line)' }}>
                            {VALUE_TILES.map((t) => (
                                <div key={t.title}>
                                    <Icon name={t.icon} size={19} color="var(--clay)" />
                                    <div style={{ marginTop: 6, fontSize: 12.5, fontWeight: 600 }}>{t.title}</div>
                                    <div style={{ marginTop: 2, fontSize: 11.5, lineHeight: 1.5, color: 'var(--subtle)' }}>{t.sub}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 18, maxWidth: 820 }}>
                        {messages.map((m, i) => <Bubble key={`${m.role}-${i}`} role={m.role} content={m.content} />)}
                        {isStreaming && streamContent && <Bubble role="assistant" content={streamContent} />}
                        {isStreaming && !streamContent && <ProcessingCard status={agentStatus} />}
                        <div ref={endRef} />
                    </div>
                )}
            </div>

            <div style={{ padding: '14px 18px 18px', borderTop: '1px solid var(--line)', background: 'var(--soft)' }}>
                <div style={{ border: '1px solid var(--line)', borderRadius: 14, background: 'var(--surface)', boxShadow: '0 1px 2px rgb(22 29 28 / .05)' }}>
                    <textarea
                        ref={taRef}
                        rows={2}
                        value={text}
                        disabled={isStreaming}
                        onChange={(e) => setText(e.target.value)}
                        onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
                        placeholder="Mô tả chuyến đi, hoặc bảo mình đổi gì — “bỏ Bà Nà, thêm 1 ngày Hội An”…"
                        style={{ width: '100%', minHeight: 62, maxHeight: 150, padding: '13px 15px 4px', border: 0, outline: 0, resize: 'none', background: 'transparent', fontSize: 14, lineHeight: 1.5 }}
                    />
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, padding: '6px 10px 10px' }}>
                        <span style={{ fontSize: 11, color: 'var(--subtle)' }}>Enter để gửi · Shift+Enter xuống dòng</span>
                        <button type="button" onClick={send} disabled={isStreaming || !text.trim()} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, minHeight: 34, padding: '0 14px', borderRadius: 999, background: text.trim() && !isStreaming ? 'var(--pri)' : 'var(--muted)', color: text.trim() && !isStreaming ? 'var(--on-pri)' : 'var(--subtle)', fontSize: 12.5, fontWeight: 600 }}>
                            Gửi<Icon name="arrow_upward" size={16} />
                        </button>
                    </div>
                </div>
            </div>
        </section>
    );
}

const hdrBtn = { display: 'grid', placeItems: 'center', width: 32, height: 32, border: '1px solid var(--line)', borderRadius: 8, color: 'var(--dim)' };
