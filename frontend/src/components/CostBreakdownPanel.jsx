const money = (v, currency = 'VND') =>
    v == null ? '—' : `${new Intl.NumberFormat('vi-VN').format(v)} ${currency}`;

const STATUS_CONFIG = {
    under_budget: { label: 'Dưới ngân sách', className: 'badge-success' },
    near_limit: { label: 'Gần hết', className: 'badge-warning' },
    slightly_over: { label: 'Hơi vượt', className: 'badge-warning' },
    over_budget: { label: 'Vượt ngân sách', className: 'badge-danger' },
    unknown: { label: 'Chưa rõ', className: 'badge-neutral' },
};

const COST_LABELS = {
    flights: 'Vé máy bay',
    hotels: 'Khách sạn',
    food: 'Ăn uống',
    local_transport: 'Di chuyển',
    tickets: 'Vé tham quan',
    buffer: 'Dự phòng',
};

export default function CostBreakdownPanel({ decision, plan }) {
    if (!decision) return null;
    const { cost_breakdown, total_cost, total_cost_per_person, budget_status, budget_delta } = decision;
    const currency = plan?.currency || 'VND';
    const cfg = STATUS_CONFIG[budget_status] || STATUS_CONFIG.unknown;

    return (
        <section className="workspace-section cost-panel" aria-label="Chi phí chi tiết">
            <h3>Chi phí</h3>

            <div className="cost-summary">
                <div className="cost-total">
                    <span className="cost-total-label">Tổng chi phí</span>
                    <span className="cost-total-value">{money(total_cost, currency)}</span>
                </div>
                <div className="cost-per-person">
                    <span>Mỗi người</span>
                    <strong>{money(total_cost_per_person, currency)}</strong>
                </div>
                <div className="cost-status">
                    <span className={`budget-badge ${cfg.className}`}>{cfg.label}</span>
                    {budget_delta != null && (
                        <span className={`budget-delta ${budget_delta > 0 ? 'over' : 'under'}`}>
                            {budget_delta > 0 ? '+' : ''}{money(budget_delta, currency)}
                        </span>
                    )}
                </div>
            </div>

            {cost_breakdown && (
                <ul className="cost-detail-list">
                    {Object.entries(cost_breakdown).map(([key, value]) => (
                        <li key={key}>
                            <span className="cost-detail-label">{COST_LABELS[key] || key}</span>
                            <strong className="cost-detail-value">{money(value, currency)}</strong>
                        </li>
                    ))}
                </ul>
            )}

            {decision.assumptions?.length > 0 && (
                <details className="cost-assumptions">
                    <summary>Giả định chi phí</summary>
                    <ul>
                        {decision.assumptions.map((a, i) => <li key={i}>{a}</li>)}
                    </ul>
                </details>
            )}

            {decision.data_freshness && Object.keys(decision.data_freshness).length > 0 && (
                <div className="data-freshness">
                    {Object.entries(decision.data_freshness).map(([k, v]) => (
                        <span key={k} className="freshness-tag">
                            {COST_LABELS[k] || k}: {new Date(v).toLocaleString('vi-VN')}
                        </span>
                    ))}
                </div>
            )}
        </section>
    );
}
