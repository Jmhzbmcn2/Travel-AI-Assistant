const API_BASE = '';

export async function sendMessage(message, sessionId, onChunk, onDone, onError) {
    try {
        const response = await fetch(`${API_BASE}/api/chat/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, session_id: sessionId }),
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let newSessionId = sessionId;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                const jsonStr = line.slice(6).trim();
                if (!jsonStr) continue;

                try {
                    const data = JSON.parse(jsonStr);
                    if (data.type === 'session') {
                        newSessionId = data.session_id;
                    } else if (data.type === 'chunk') {
                        onChunk(data.content);
                    } else if (data.type === 'done') {
                        onDone(newSessionId);
                    } else if (data.type === 'error') {
                        onError(data.content);
                    }
                } catch {
                    // skip malformed JSON
                }
            }
        }
    } catch (err) {
        onError(err.message);
    }
}

export async function fetchSessions() {
    const res = await fetch(`${API_BASE}/api/sessions`);
    if (!res.ok) return [];
    return res.json();
}

export async function fetchSessionMessages(sessionId) {
    const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.messages || [];
}

export async function deleteSession(sessionId) {
    await fetch(`${API_BASE}/api/sessions/${sessionId}`, { method: 'DELETE' });
}
