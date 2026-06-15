import { useState } from 'react';

const SEVERITY_CONFIG = {
    high: { icon: '🔴', label: 'Cao', className: 'risk-high' },
    medium: { icon: '🟡', label: 'Trung bình', className: 'risk-medium' },
    low: { icon: '🟢', label: 'Thấp', className: 'risk-low' },
};

export default function RiskPanel({ risks, assumptions }) {
    const [showAssumptions, setShowAssumptions] = useState(false);

    if ((!risks || risks.length === 0) && (!assumptions || assumptions.length === 0)) return null;

    const grouped = { high: [], medium: [], low: [] };
    (risks || []).forEach((risk) => {
        const sev = risk.severity || 'medium';
        if (grouped[sev]) grouped[sev].push(risk);
        else grouped.medium.push(risk);
    });

    return (
        <section className="workspace-section risk-panel" aria-label="Rủi ro và giả định">
            <h3>Rủi ro và cảnh báo</h3>

            {['high', 'medium', 'low'].map((severity) => {
                const items = grouped[severity];
                if (!items || items.length === 0) return null;
                const cfg = SEVERITY_CONFIG[severity];
                return (
                    <div className={`risk-group ${cfg.className}`} key={severity}>
                        <h4>
                            {cfg.icon} {cfg.label} ({items.length})
                        </h4>
                        <ul className="risk-list">
                            {items.map((risk, i) => (
                                <li className="risk-item" key={`${risk.type}-${i}`}>
                                    <span className="risk-message">{risk.message}</span>
                                    {risk.recommendation && (
                                        <span className="risk-recommendation">
                                            💡 {risk.recommendation}
                                        </span>
                                    )}
                                </li>
                            ))}
                        </ul>
                    </div>
                );
            })}

            {assumptions?.length > 0 && (
                <div className="assumptions-section">
                    <button
                        type="button"
                        className="assumptions-toggle"
                        onClick={() => setShowAssumptions(!showAssumptions)}
                    >
                        {showAssumptions ? '▼' : '▶'} Giả định ({assumptions.length})
                    </button>
                    {showAssumptions && (
                        <ul className="assumptions-list">
                            {assumptions.map((a, i) => (
                                <li key={i}>{a}</li>
                            ))}
                        </ul>
                    )}
                </div>
            )}
        </section>
    );
}
