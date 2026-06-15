export default function ChatBubble({ role, content }) {
    const isAssistant = role === 'assistant';

    return (
        <div className={`bubble-row ${role}`}>
            <div className={`bubble-avatar ${role}`}>
                <span className={`material-symbols-outlined ${isAssistant ? 'icon-fill' : ''}`}>
                    {isAssistant ? 'smart_toy' : 'person'}
                </span>
            </div>
            <div className={`bubble ${role}`}>
                {isAssistant ? (
                    <div className="md-content" dangerouslySetInnerHTML={{ __html: formatMarkdown(content) }} />
                ) : (
                    <span>{content}</span>
                )}
            </div>
        </div>
    );
}

export function InterruptBubble({ message, onConfirm, onModify, disabled }) {
    return (
        <div className="bubble-row assistant">
            <div className="bubble-avatar assistant">
                <span className="material-symbols-outlined icon-fill">smart_toy</span>
            </div>
            <div className="assistant-stack">
                <div className="bubble assistant">
                    <div className="md-content" dangerouslySetInnerHTML={{ __html: formatMarkdown(message) }} />
                </div>
                <div className="interrupt-card">
                    <h3>Xác nhận bản nháp kế hoạch?</h3>
                    <p>Bạn có thể điều chỉnh thêm ở bảng chi tiết bên phải.</p>
                    <div className="interrupt-actions">
                        <button className="interrupt-btn confirm" type="button" onClick={() => onConfirm('ok')} disabled={disabled}>
                            Xác nhận
                        </button>
                        <button className="interrupt-btn modify" type="button" onClick={onModify} disabled={disabled}>
                            Thay đổi
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

function formatMarkdown(text) {
    if (!text) return '';

    let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    html = html.replace(/`(.+?)`/g, '<code>$1</code>');

    html = html.replace(/^####\s+(.+)$/gm, '<h4>$1</h4>');
    html = html.replace(/^###\s+(.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^##\s+(.+)$/gm, '<h3>$1</h3>');

    html = html.replace(/^[-•]\s+(.+)$/gm, '<li>$1</li>');
    html = html.replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>');
    html = html.replace(/((?:<li>.*?<\/li>\s*)+)/g, '<ul>$1</ul>');

    html = html.replace(/\n\n/g, '</p><p>');
    html = html.replace(/\n/g, '<br/>');

    html = html.replace(/<br\/?>\s*<ul>/g, '<ul>');
    html = html.replace(/<\/ul>\s*<br\/?>/g, '</ul>');
    html = html.replace(/<br\/?>\s*<li>/g, '<li>');
    html = html.replace(/<br\/?>\s*<h/g, '<h');
    html = html.replace(/<\/h(\d)>\s*<br\/?>/g, '</h$1>');

    return `<p>${html}</p>`;
}
