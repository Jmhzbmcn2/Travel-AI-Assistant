const money = (v, currency = 'VND') =>
    v == null ? '—' : `${new Intl.NumberFormat('vi-VN').format(v)} ${currency}`;

// Removed ScoreLabel component to avoid pseudo-precision

const OPTION_LABELS = {
    cheapest: 'Tiết kiệm',
    balanced: 'Cân bằng',
    comfortable: 'Thoải mái',
};

export default function OptionComparison({ options, recommendedId, currency = 'VND', decisionStatus }) {
    if (!options || options.length === 0) return null;

    const showRecommendation = decisionStatus === 'recommended' && recommendedId != null;

    return (
        <section className="workspace-section option-comparison" aria-label="So sánh phương án">
            <h3>So sánh phương án</h3>

            {!showRecommendation && (
                <div className="comparison-notice">
                    <span className="material-symbols-outlined">info</span>
                    Chưa đủ dữ liệu xác minh để khuyến nghị phương án.
                </div>
            )}

            <div className="comparison-grid">
                {options.map((opt) => {
                    const isRec = showRecommendation && opt.id === recommendedId;
                    return (
                        <article
                            className={`comparison-card ${isRec ? 'recommended' : ''}`}
                            key={opt.id}
                        >
                            <header className="comparison-header">
                                <strong>{OPTION_LABELS[opt.id] || opt.id}</strong>
                                {isRec && <span className="rec-badge">Khuyến nghị</span>}
                            </header>

                            <div className="comparison-cost">
                                <span className="big-cost">{money(opt.total_cost, currency)}</span>
                            </div>

                            <div className="comparison-status" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem', fontSize: '0.9rem' }}>
                                <div className="status-item" style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span className="status-label" style={{ color: 'var(--text-muted)' }}>Mức độ khả thi:</span>
                                    <span className="status-value" style={{ fontWeight: '500' }}>{opt.feasibility_status || 'Không đủ dữ liệu'}</span>
                                </div>
                                <div className="status-item" style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span className="status-label" style={{ color: 'var(--text-muted)' }}>Mức độ thoải mái:</span>
                                    <span className="status-value" style={{ fontWeight: '500' }}>{opt.comfort_status || 'Cơ bản'}</span>
                                </div>
                            </div>

                            {opt.cost_breakdown && (
                                <details className="comparison-breakdown">
                                    <summary>Chi tiết chi phí</summary>
                                    <ul className="mini-cost-list">
                                        {Object.entries(opt.cost_breakdown).map(([k, v]) => (
                                            <li key={k}>
                                                <span>{k}</span>
                                                <span>{money(v, currency)}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </details>
                            )}

                            {opt.tradeoffs?.length > 0 && (
                                <div className="comparison-tradeoffs">
                                    {opt.tradeoffs.map((t) => (
                                        <span className="tradeoff-tag" key={t}>
                                            {t}
                                        </span>
                                    ))}
                                </div>
                            )}

                            {opt.reasons?.length > 0 && (
                                <ul className="comparison-reasons">
                                    {opt.reasons.map((r, i) => (
                                        <li key={i}>{r}</li>
                                    ))}
                                </ul>
                            )}
                        </article>
                    );
                })}
            </div>
        </section>
    );
}
