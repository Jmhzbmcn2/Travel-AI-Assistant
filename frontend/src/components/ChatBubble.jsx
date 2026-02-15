export default function ChatBubble({ role, content }) {
    return (
        <div className={`bubble-row ${role}`}>
            <div className={`bubble-avatar ${role}`}>
                {role === 'assistant' ? '✈️' : '👤'}
            </div>
            <div className={`bubble ${role}`}>
                {role === 'assistant' ? (
                    <div className="md-content" dangerouslySetInnerHTML={{ __html: formatMarkdown(content) }} />
                ) : (
                    <span>{content}</span>
                )}
            </div>
        </div>
    );
}

function formatMarkdown(text) {
    if (!text) return '';

    // Escape HTML first
    let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    // Code blocks (triple backtick)
    html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');

    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    // Italic
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    // Inline code
    html = html.replace(/`(.+?)`/g, '<code>$1</code>');

    // Headers
    html = html.replace(/^####\s+(.+)$/gm, '<h4>$1</h4>');
    html = html.replace(/^###\s+(.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^##\s+(.+)$/gm, '<h3>$1</h3>');

    // Unordered list items
    html = html.replace(/^[-•]\s+(.+)$/gm, '<li>$1</li>');
    // Numbered list items
    html = html.replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>');

    // Wrap consecutive <li> in <ul>
    html = html.replace(/((?:<li>.*?<\/li>\s*)+)/g, '<ul>$1</ul>');

    // Paragraphs
    html = html.replace(/\n\n/g, '</p><p>');
    html = html.replace(/\n/g, '<br/>');

    // Clean up BR inside/around lists
    html = html.replace(/<br\/?>\s*<ul>/g, '<ul>');
    html = html.replace(/<\/ul>\s*<br\/?>/g, '</ul>');
    html = html.replace(/<br\/?>\s*<li>/g, '<li>');
    html = html.replace(/<br\/?>\s*<h/g, '<h');
    html = html.replace(/<\/h(\d)>\s*<br\/?>/g, '</h$1>');

    return `<p>${html}</p>`;
}
