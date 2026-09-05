export const money = (value) => {
    if (value == null) return 'chưa có';
    return `${new Intl.NumberFormat('vi-VN').format(Math.round(Math.abs(value)))} ₫`;
};

const esc = (t) => t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

export function formatMarkdown(text) {
    if (!text) return '';
    let html = esc(text);
    html = html.replace(/```([\s\S]*?)```/g, (_, c) => `<pre><code>${c}</code></pre>`);
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/`([^`]+?)`/g, '<code>$1</code>');
    html = html.replace(/^###\s+(.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^##\s+(.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^\s*(?:[-•↳]|⚠️)\s+(.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>[\s\S]*?<\/li>)(?!\s*<li>)/g, '<ul>$1</ul>');
    html = html.replace(/\n{2,}/g, '</p><p>');
    html = html.replace(/\n/g, '<br/>');
    html = html.replace(/<br\/?>\s*(<\/?(?:ul|li|h3|pre)>)/g, '$1');
    html = html.replace(/(<\/(?:ul|li|h3|pre)>)\s*<br\/?>/g, '$1');
    return `<p>${html}</p>`;
}
