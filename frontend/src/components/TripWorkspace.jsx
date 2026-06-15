import CostBreakdownPanel from './CostBreakdownPanel';
import ItineraryTimeline from './ItineraryTimeline';
import OptionComparison from './OptionComparison';
import PlanEditor from './PlanEditor';
import RiskPanel from './RiskPanel';

const money = (value, currency = 'VND') => value == null ? 'Chưa có' : `${new Intl.NumberFormat('vi-VN').format(value)} ${currency}`;

const STATUS_CONFIG = {
    recommended: { label: 'Khả thi', className: 'success' },
    needs_revision: { label: 'Cần chỉnh sửa', className: 'warning' },
    insufficient_data: { label: 'Không đủ dữ liệu', className: 'error' },
};

const COVERAGE_LABELS = {
    verified: 'Dữ liệu xác minh',
    draft_only: 'Bản nháp',
    unsupported: 'Chưa hỗ trợ',
};

export default function TripWorkspace({
    workspace,
    sessionId,
    onConfirm,
    editing,
    onEdit,
    onSavePlan,
    onCancelEdit,
    savingPlan,
    isCollapsed,
    onToggleCollapse,
    onTripAction,
    loadingAction,
}) {
    const plan = workspace?.plan;
    const decision = workspace?.decision;
    const missing = workspace?.missing_fields || [];

    const decisionStatus = decision?.decision_status || 'insufficient_data';
    const statusConfig = STATUS_CONFIG[decisionStatus] || STATUS_CONFIG.insufficient_data;
    const coverageStatus = decision?.coverage_status;

    return (
        <aside className={`decision-canvas ${isCollapsed ? 'collapsed' : ''}`} aria-label="Trip decision canvas">
            <header className="decision-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
                    <h2>{plan?.destination ? `Chuyến đi ${plan.destination}` : 'Kế hoạch chuyến đi'}</h2>
                    <button
                        className="header-menu"
                        type="button"
                        title="Thu gọn"
                        onClick={onToggleCollapse}
                        style={{ flexShrink: 0 }}
                    >
                        <span className="material-symbols-outlined">right_panel_close</span>
                    </button>
                </div>
                <div className="trip-meta">
                    <span>{plan?.days ? `${plan.days} ngày` : 'Chưa đủ ngày'}</span>
                    <span>·</span>
                    <span>{plan?.travelers || 1} người</span>
                    <span>·</span>
                    <span>{money(plan?.budget_total, plan?.currency)}</span>
                </div>
                {decision && (
                    <div className="summary-strip">
                        <span className={`summary-pill ${statusConfig.className}`}>{statusConfig.label}</span>
                        <span className="summary-pill info">{money(decision.total_cost, plan?.currency)}</span>
                        <span className="summary-pill warning">{decision.risks.length} cảnh báo</span>
                        {coverageStatus && (
                            <span className={`data-mode-badge ${coverageStatus}`}>{COVERAGE_LABELS[coverageStatus] || coverageStatus}</span>
                        )}
                    </div>
                )}
            </header>

            <div className="decision-scroll">
                {editing && plan && <PlanEditor plan={plan} onSave={onSavePlan} onCancel={onCancelEdit} saving={savingPlan} />}

                {!plan && <div className="workspace-empty">Bắt đầu bằng cách mô tả chuyến đi trong khung chat.</div>}

                {plan && !editing && (
                    <section className="workspace-section">
                        <div className="section-heading">
                            <h3>Bản nháp kế hoạch</h3>
                            {workspace?.status !== 'decided' && <button type="button" onClick={onEdit}>Chỉnh sửa</button>}
                        </div>
                        <dl className="plan-summary">
                            <div><dt>Điểm đi</dt><dd>{plan.origin || 'Chưa có'}</dd></div>
                            <div><dt>Điểm đến</dt><dd>{plan.destination || 'Chưa có'}</dd></div>
                            <div><dt>Thời gian</dt><dd>{plan.departure_date || 'Chưa có'} → {plan.return_date || 'Chưa có'}</dd></div>
                            <div><dt>Sở thích</dt><dd>{plan.preferences?.join(', ') || 'Chưa có'}</dd></div>
                            <div><dt>Ưu tiên</dt><dd>
                                {plan.priority === 'less_travel' ? 'Di chuyển ít' : 
                                 plan.priority === 'comfortable' ? 'Thoải mái nhất' : 'Tiết kiệm nhất'}
                            </dd></div>
                        </dl>
                        {missing.length > 0 && <p className="workspace-warning">Còn thiếu: {missing.join(', ')}</p>}
                    </section>
                )}

                {/* Blocking reasons when recommendation is not possible */}
                {decision?.blocking_reasons?.length > 0 && (
                    <section className="workspace-section blocking-reasons-section">
                        <h3>Lý do chưa thể khuyến nghị</h3>
                        <ul className="blocking-reasons-list">
                            {decision.blocking_reasons.map((reason, i) => (
                                <li key={i} className="blocking-reason-item">
                                    <span className="material-symbols-outlined blocking-icon">warning</span>
                                    {reason}
                                </li>
                            ))}
                        </ul>
                    </section>
                )}
                
                {decision?.decision_status === 'needs_revision' && decision.itinerary?.some(d => d.evidence?.length > 0) && (
                    <section className="workspace-section evidence-summary-section">
                        <h3>Tại sao cần chỉnh sửa?</h3>
                        <ul className="blocking-reasons-list">
                            {decision.itinerary.flatMap(d => d.evidence || []).map((ev, i) => (
                                <li key={i} className="blocking-reason-item">
                                    <span className="material-symbols-outlined blocking-icon">info</span>
                                    <strong>{ev.rule}:</strong> {ev.recommendation} ({ev.observed_value})
                                </li>
                            ))}
                        </ul>
                    </section>
                )}

                {decision && (
                    <>
                        <OptionComparison
                            options={decision.options}
                            recommendedId={decision.recommended_option}
                            currency={plan?.currency}
                            decisionStatus={decision.decision_status}
                        />

                        <CostBreakdownPanel decision={decision} plan={plan} />

                        <ItineraryTimeline
                            itinerary={decision.itinerary}
                            currency={plan?.currency}
                            onAction={onTripAction}
                            loadingAction={loadingAction}
                        />

                        <RiskPanel
                            risks={decision.risks}
                            assumptions={decision.assumptions}
                        />
                    </>
                )}
            </div>

            <footer className="decision-actions">
                <button className="primary-action" type="button" disabled={workspace?.status !== 'awaiting_confirmation' || missing.length > 0 || editing} onClick={() => onConfirm?.('ok')}>
                    Xác nhận kế hoạch
                </button>
                {sessionId && <a className="secondary-action" href={`/api/v1/trips/${sessionId}/export.md`}>Xuất Markdown</a>}
                {sessionId && (
                    <button className="secondary-action" type="button" onClick={() => window.print()}>
                        Xuất PDF / In
                    </button>
                )}
                {decision?.decision_status === 'recommended' && decision?.booking_links?.map((link) => <a className="secondary-action" href={link} target="_blank" rel="noreferrer" key={link}>Mở trang đặt chỗ</a>)}
            </footer>
        </aside>
    );
}
