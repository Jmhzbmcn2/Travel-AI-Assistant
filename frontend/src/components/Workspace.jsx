import { Icon } from '../lib/ui';
import { money } from '../lib/format';
import PlanEditor from './PlanEditor';

const STATUS = {
    recommended: { label: 'Có thể đặt chỗ', color: 'var(--ok)', soft: 'var(--ok-soft)', line: 'var(--ok-line)', icon: 'check_circle' },
    needs_revision: { label: 'Khả thi có điều kiện — cần sửa', color: 'var(--warn)', soft: 'var(--warn-soft)', line: 'var(--warn-line)', icon: 'rule' },
    insufficient_data: { label: 'Chưa đủ dữ liệu để quyết định', color: 'var(--dgr)', soft: 'var(--dgr-soft)', line: 'var(--dgr-line)', icon: 'error' },
};
const CONFIDENCE_BARS = { high: 3, medium: 2, low: 1, insufficient: 1 };
const BUDGET = {
    under_budget: { label: 'Dưới ngân sách', tone: 'ok' },
    near_limit: { label: 'Sát ngân sách', tone: 'warn' },
    slightly_over: { label: 'Hơi vượt', tone: 'warn' },
    over_budget: { label: 'Vượt ngân sách', tone: 'dgr' },
    unknown: { label: 'Chưa rõ ngân sách', tone: 'subtle' },
};
const OPTION = { cheapest: 'Tiết kiệm', balanced: 'Cân bằng', comfortable: 'Thoải mái' };
const TRUST = {
    verified: { label: 'Đã xác thực', dot: 'var(--pri)' },
    estimated: { label: 'Ước tính', dot: 'var(--warn)' },
    unverified: { label: 'Chưa kiểm chứng', dot: 'transparent', ring: true },
    fixture: { label: 'Dữ liệu demo', dot: 'var(--clay)' },
    missing: { label: 'Thiếu dữ liệu', dot: 'transparent', ring: true },
};
const CAT_ICON = {
    food: 'restaurant', restaurant: 'restaurant', attraction: 'photo_camera', culture: 'account_balance',
    beach: 'beach_access', nature: 'forest', shopping: 'shopping_bag', nightlife: 'nightlife',
    hotel: 'hotel', rest: 'bedtime',
};
const MODE_ICON = { driving: 'directions_car', transit: 'directions_transit', walking: 'directions_walk' };
const SEV = {
    high: { label: 'Chặn lại — phải xử lý', color: 'var(--dgr)', soft: 'var(--dgr-soft)', line: 'var(--dgr-line)', icon: 'error' },
    medium: { label: 'Nên kiểm tra', color: 'var(--warn)', soft: 'var(--soft)', line: 'var(--line)', icon: 'warning' },
    low: { label: 'Ghi nhận, không đáng lo', color: 'var(--subtle)', soft: 'var(--soft)', line: 'var(--line)', icon: 'info' },
};
const COST_LABEL = {
    flights: 'Vé máy bay', hotels: 'Khách sạn', food: 'Ăn uống',
    local_transport: 'Di chuyển', tickets: 'Vé tham quan', buffer: 'Dự phòng',
};
const COST_COLOR = ['var(--cost-1)', 'var(--cost-2)', 'var(--cost-3)', 'var(--cost-4)', 'var(--cost-5)', 'var(--line-2)'];

const chip = { display: 'inline-flex', alignItems: 'center', gap: 5, padding: '4px 9px', border: '1px solid var(--line)', borderRadius: 7, background: 'var(--surface)', fontSize: 11.5, fontWeight: 500, color: 'var(--dim)' };
const h3s = { fontSize: 14, fontWeight: 600, letterSpacing: '-.01em' };
const eyebrow = { fontSize: 10.5, fontWeight: 600, letterSpacing: '.06em', textTransform: 'uppercase', color: 'var(--subtle)' };

function TrustBadge({ status }) {
    const t = TRUST[status] || TRUST.unverified;
    return (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '3px 8px', border: '1px solid var(--line)', borderRadius: 6, background: 'var(--soft)', fontSize: 10.5, fontWeight: 500, color: 'var(--dim)', whiteSpace: 'nowrap' }}>
            <span style={{ width: 7, height: 7, borderRadius: '50%', background: t.dot, border: t.ring ? '1.5px solid var(--line-2)' : 'none' }} />{t.label}
        </span>
    );
}

function PlaceCard({ place, onAction, loadingAction }) {
    const busy = loadingAction?.action === 'replace_place' && loadingAction?.target === place.place_id;
    return (
        <article style={{ display: 'flex', gap: 11, padding: 11, border: '1px solid var(--line)', borderRadius: 12, background: 'var(--surface)' }}>
            <div style={{ width: 52, height: 52, flex: '0 0 52px', borderRadius: 9, display: 'grid', placeItems: 'center', background: 'repeating-linear-gradient(135deg,var(--muted) 0 5px,var(--soft) 5px 10px)' }}>
                <Icon name={CAT_ICON[place.category] || 'place'} size={20} color="var(--subtle)" />
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 9 }}>
                    <div style={{ minWidth: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 10.5, fontWeight: 600, letterSpacing: '.05em', textTransform: 'uppercase', color: 'var(--clay)' }}>
                            <Icon name={CAT_ICON[place.category] || 'place'} size={13} />{place.category || 'điểm đến'}
                        </div>
                        <h4 style={{ margin: '3px 0 0', fontSize: 13.5, fontWeight: 600, lineHeight: 1.35 }}>{place.title}</h4>
                        {place.area && <div style={{ marginTop: 2, fontSize: 11.5, color: 'var(--subtle)' }}>{place.area}</div>}
                    </div>
                    <TrustBadge status={place.confidence || 'unverified'} />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginTop: 9, paddingTop: 9, borderTop: '1px solid var(--line)' }}>
                    <span className="mono" style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 11.5, color: 'var(--dim)' }}>
                        <Icon name="timer" size={14} color="var(--subtle)" />{place.estimated_visit_minutes || '—'} phút
                    </span>
                    {place.estimated_cost > 0 && (
                        <span className="mono" style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 11.5, color: 'var(--dim)' }}>
                            <Icon name="payments" size={14} color="var(--subtle)" />{money(place.estimated_cost)}
                        </span>
                    )}
                    <span style={{ flex: 1 }} />
                    {place.maps_url && (
                        <a href={place.maps_url} target="_blank" rel="noopener noreferrer" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 11.5, fontWeight: 600 }}>
                            <Icon name="map" size={14} />Maps
                        </a>
                    )}
                    {onAction && (
                        <button type="button" disabled={!!loadingAction} onClick={() => onAction('replace_place', null, place.place_id)} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 11.5, fontWeight: 600, color: 'var(--dim)' }}>
                            <Icon name="swap_horiz" size={14} />{busy ? 'Đang tìm…' : 'Thay'}
                        </button>
                    )}
                </div>
            </div>
        </article>
    );
}

function RouteLeg({ leg }) {
    const unverified = leg.confidence === 'unverified' || leg.duration_minutes == null;
    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: 9, margin: '0 0 0 26px', padding: '7px 0 7px 16px', borderLeft: '1px dashed var(--line-2)' }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '3px 9px', borderRadius: 999, background: 'var(--muted)', fontSize: 11, fontWeight: 500, color: 'var(--dim)' }}>
                <Icon name={MODE_ICON[leg.mode] || 'directions_car'} size={14} />
                {unverified ? 'chưa có dữ liệu' : `${leg.distance_km ?? '—'} km · ${leg.duration_minutes} phút`}
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 10.5, color: 'var(--subtle)' }}>
                <span style={{ width: 7, height: 7, borderRadius: '50%', background: unverified ? 'transparent' : leg.confidence === 'estimated' ? 'var(--warn)' : 'var(--pri)', border: unverified ? '1.5px solid var(--line-2)' : 'none' }} />
                {unverified ? 'Chưa kiểm chứng' : leg.confidence === 'estimated' ? 'Ước tính' : 'Đã xác thực'}
            </span>
            {leg.directions_url && !unverified && (
                <a href={leg.directions_url} target="_blank" rel="noopener noreferrer" style={{ fontSize: 10.5, fontWeight: 600 }}>Chỉ đường</a>
            )}
        </div>
    );
}

function Overview({ workspace, decision, plan, onEdit, editing, onSavePlan, onCancelEdit, savingPlan }) {
    const missing = workspace?.missing_fields || [];
    const options = decision?.options || [];
    const recId = decision?.recommended_option;
    const showRec = decision?.decision_status === 'recommended' && recId;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {editing ? (
                <PlanEditor plan={plan} onSave={onSavePlan} onCancel={onCancelEdit} saving={savingPlan} />
            ) : (
                <>
                    {missing.length > 0 && (
                        <section style={{ padding: 15, border: '1px solid var(--pri-line)', borderRadius: 13, background: 'var(--pri-soft)' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <Icon name="edit_note" size={18} color="var(--pri)" />
                                <h3 style={{ flex: 1, fontSize: 13.5, fontWeight: 600, color: 'var(--pri)' }}>Còn thiếu {missing.length} mục để mình chốt được</h3>
                            </div>
                            <p style={{ margin: '6px 0 10px 26px', fontSize: 12, lineHeight: 1.55, color: 'var(--dim)' }}>
                                Thiếu các thông tin này nên kết quả vẫn ở dạng bản nháp.
                            </p>
                            <ul style={{ margin: '0 0 10px 26px', display: 'grid', gap: 4, fontSize: 12.5, color: 'var(--dim)', listStyle: 'disc' }}>
                                {missing.map((f) => <li key={f}>{MISSING_LABEL[f] || f}</li>)}
                            </ul>
                            <button type="button" onClick={onEdit} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, minHeight: 34, padding: '0 13px', borderRadius: 8, background: 'var(--pri)', color: 'var(--on-pri)', fontSize: 12.5, fontWeight: 600 }}>
                                <Icon name="edit" size={15} />Bổ sung thông tin
                            </button>
                        </section>
                    )}

                    {options.length > 0 && (
                        <section>
                            <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 10, marginBottom: 10 }}>
                                <h3 style={h3s}>{options.length === 1 ? 'Phương án' : `${options.length} phương án`}</h3>
                                <span style={{ fontSize: 11.5, color: 'var(--subtle)' }}>Giá là ước tính, chưa khoá</span>
                            </div>
                            <div style={{ display: 'grid', gap: 8 }}>
                                {options.map((o) => {
                                    const rec = showRec && o.id === recId;
                                    return (
                                        <article key={o.id} style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '10px 14px', padding: '13px 14px', border: rec ? '1.5px solid var(--pri)' : '1px solid var(--line)', borderRadius: 12, background: rec ? 'var(--surface)' : 'var(--soft)', boxShadow: rec ? '0 2px 10px rgb(18 95 92 / .08)' : 'none' }}>
                                            <div style={{ minWidth: 0 }}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: 7, flexWrap: 'wrap' }}>
                                                    <span style={{ fontSize: 13.5, fontWeight: 600 }}>{OPTION[o.id] || o.id}</span>
                                                    {rec ? (
                                                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '2px 8px', borderRadius: 6, background: 'var(--pri)', color: 'var(--on-pri)', fontSize: 10.5, fontWeight: 600 }}>
                                                            <Icon name="star" size={12} />Khuyến nghị
                                                        </span>
                                                    ) : (
                                                        <span style={{ padding: '2px 7px', borderRadius: 6, background: 'var(--muted)', fontSize: 10.5, fontWeight: 600, color: 'var(--dim)' }}>{o.feasibility_status}</span>
                                                    )}
                                                </div>
                                                {o.reasons?.[0] && <div style={{ marginTop: 5, fontSize: 12, lineHeight: 1.5, color: 'var(--dim)' }}>{o.reasons[0]}</div>}
                                                {o.tradeoffs?.length > 0 && (
                                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 8 }}>
                                                        {o.tradeoffs.slice(0, 4).map((t) => (
                                                            <span key={t} style={{ padding: '3px 8px', borderRadius: 6, background: rec ? 'var(--pri-soft)' : 'var(--muted)', fontSize: 10.5, fontWeight: 500, color: rec ? 'var(--pri)' : 'var(--dim)' }}>{t}</span>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                            <div style={{ textAlign: 'right' }}>
                                                <div className="mono" style={{ fontSize: 16, fontWeight: 500, color: rec ? 'var(--pri)' : 'var(--text)' }}>{money(o.total_cost)}</div>
                                                <div style={{ marginTop: 2, fontSize: 11, color: 'var(--subtle)' }}>{o.comfort_status || 'Cơ bản'}</div>
                                            </div>
                                        </article>
                                    );
                                })}
                            </div>
                        </section>
                    )}

                    {plan && (
                        <section>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, marginBottom: 8 }}>
                                <h3 style={h3s}>Kế hoạch đang dùng</h3>
                                <button type="button" onClick={onEdit} style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '5px 10px', border: '1px solid var(--line)', borderRadius: 7, fontSize: 11.5, fontWeight: 600, color: 'var(--dim)' }}>
                                    <Icon name="edit" size={14} />Chỉnh sửa
                                </button>
                            </div>
                            <dl style={{ display: 'grid' }}>
                                <PlanRow k="Điểm đi → đến" v={`${plan.origin || '—'} → ${plan.destination || '—'}`} />
                                <PlanRow k="Thời gian" v={`${plan.departure_date || '—'} → ${plan.return_date || '—'}`} />
                                <PlanRow k="Sở thích" v={plan.preferences?.join(' · ') || '—'} />
                                <PlanRow k="Ưu tiên" v={PRIORITY[plan.priority] || plan.priority} />
                            </dl>
                        </section>
                    )}
                </>
            )}
        </div>
    );
}

const PlanRow = ({ k, v }) => (
    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 14, padding: '8px 0', borderTop: '1px solid var(--line)' }}>
        <dt style={{ fontSize: 12, color: 'var(--subtle)' }}>{k}</dt>
        <dd style={{ margin: 0, fontSize: 12.5, fontWeight: 500, textAlign: 'right' }}>{v}</dd>
    </div>
);
const MISSING_LABEL = { origin: 'Điểm đi', destination: 'Điểm đến', days_or_date_range: 'Số ngày hoặc khoảng ngày', budget: 'Ngân sách', preferences: 'Sở thích', comfort_level: 'Mức thoải mái', travelers: 'Số người' };
const PRIORITY = { cheapest: 'Tiết kiệm nhất', less_travel: 'Di chuyển ít', comfortable: 'Thoải mái nhất' };

function Itinerary({ decision, onAction, loadingAction, diff }) {
    const days = decision?.itinerary || [];
    if (days.length === 0) return <Empty text="Chưa có lịch trình." />;
    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
            {diff && (
                <section style={{ border: '1px solid var(--pri-line)', borderRadius: 12, background: 'var(--surface)', overflow: 'hidden' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '9px 13px', background: 'var(--pri-soft)' }}>
                        <Icon name="difference" size={16} color="var(--pri)" />
                        <span style={{ flex: 1, fontSize: 12, fontWeight: 600, color: 'var(--pri)' }}>{diff}</span>
                    </div>
                </section>
            )}
            {days.map((day) => {
                const busy = loadingAction?.action === 'optimize_day' && loadingAction?.target === day.day;
                return (
                    <section key={day.day}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, marginBottom: 11 }}>
                            <div style={{ display: 'flex', alignItems: 'baseline', gap: 9, minWidth: 0 }}>
                                <h3 style={{ ...h3s, whiteSpace: 'nowrap' }}>{day.title || `Ngày ${day.day}`}</h3>
                                {day.date && <span className="mono" style={{ fontSize: 11, color: 'var(--subtle)' }}>{day.date}</span>}
                            </div>
                            {onAction && day.items?.length > 2 ? (
                                <button type="button" disabled={!!loadingAction} onClick={() => onAction('optimize_day', day.day, null)} style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '5px 10px', border: '1px solid var(--pri-line)', borderRadius: 7, background: 'var(--pri-soft)', fontSize: 11.5, fontWeight: 600, color: 'var(--pri)' }}>
                                    <Icon name="auto_fix_high" size={14} />{busy ? 'Đang tối ưu…' : 'Tối ưu ngày'}
                                </button>
                            ) : (
                                day.travel_minutes > 0 && (
                                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 11.5, color: 'var(--dim)', whiteSpace: 'nowrap' }}>
                                        <Icon name="schedule" size={14} color="var(--subtle)" />di chuyển {day.travel_minutes} phút
                                    </span>
                                )
                            )}
                        </div>

                        {day.evidence?.length > 0 && (
                            <div style={{ display: 'grid', gap: 8, marginBottom: 10 }}>
                                {day.evidence.map((ev, i) => (
                                    <div key={i} style={{ display: 'flex', gap: 9, padding: '11px 13px', border: '1px solid var(--warn-line)', borderRadius: 11, background: 'var(--warn-soft)' }}>
                                        <Icon name="warning" size={17} color="var(--warn)" />
                                        <div style={{ minWidth: 0 }}>
                                            <div style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--warn)' }}>{ev.rule}{ev.observed_value ? ` — ${ev.observed_value}` : ''}</div>
                                            {ev.recommendation && <div style={{ marginTop: 3, fontSize: 12, lineHeight: 1.5, color: 'var(--dim)' }}>{ev.recommendation}</div>}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                            {(day.route_legs?.length ? day.route_legs : []).map((leg, i) => (
                                <div key={i}>
                                    {i < (day.items?.length || 0) && <PlaceCard place={day.items[i]} onAction={onAction} loadingAction={loadingAction} />}
                                    <RouteLeg leg={leg} />
                                    {i === day.route_legs.length - 1 && i + 1 < (day.items?.length || 0) && (
                                        <PlaceCard place={day.items[i + 1]} onAction={onAction} loadingAction={loadingAction} />
                                    )}
                                </div>
                            ))}
                            {!day.route_legs?.length && (day.items || []).map((it, i) => (
                                <PlaceCard key={i} place={it} onAction={onAction} loadingAction={loadingAction} />
                            ))}
                        </div>
                    </section>
                );
            })}
        </div>
    );
}

function Cost({ decision }) {
    const cb = decision?.cost_breakdown;
    if (!cb) return <Empty text="Chưa có dữ liệu chi phí." />;
    const entries = Object.entries(cb).filter(([, v]) => v > 0);
    const total = decision.total_cost || entries.reduce((s, [, v]) => s + v, 0);
    const b = BUDGET[decision.budget_status] || BUDGET.unknown;
    const fresh = decision.data_freshness || {};

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
            <section style={{ padding: 15, border: '1px solid var(--line)', borderRadius: 13, background: 'var(--soft)' }}>
                <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: 12 }}>
                    <div>
                        <div style={eyebrow}>Tổng chi phí</div>
                        <div className="mono" style={{ marginTop: 4, fontSize: 26, fontWeight: 500, letterSpacing: '-.02em' }}>{money(total)}</div>
                        <div style={{ marginTop: 3, fontSize: 12, color: 'var(--dim)' }}>{money(decision.total_cost_per_person)} / người</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '4px 9px', border: `1px solid var(--${b.tone === 'subtle' ? 'line' : b.tone}-line)`, borderRadius: 7, background: `var(--${b.tone === 'subtle' ? 'soft' : b.tone + '-soft'})`, fontSize: 11, fontWeight: 600, color: `var(--${b.tone === 'subtle' ? 'subtle' : b.tone})` }}>
                            <Icon name={b.tone === 'ok' ? 'check_circle' : b.tone === 'dgr' ? 'error' : 'info'} size={14} />{b.label}
                        </span>
                        {decision.budget_delta != null && (
                            <div className="mono" style={{ marginTop: 5, fontSize: 12, color: decision.budget_delta < 0 ? 'var(--ok)' : 'var(--dgr)' }}>
                                {decision.budget_delta < 0 ? 'còn dư ' : 'vượt '}{money(Math.abs(decision.budget_delta))}
                            </div>
                        )}
                    </div>
                </div>
                <div style={{ display: 'flex', height: 8, marginTop: 14, borderRadius: 999, overflow: 'hidden', background: 'var(--muted)' }}>
                    {entries.map(([k, v], i) => <div key={k} style={{ width: `${(v / total) * 100}%`, background: COST_COLOR[i % COST_COLOR.length] }} />)}
                </div>
            </section>

            <section>
                <h3 style={{ ...h3s, marginBottom: 8 }}>Từng khoản</h3>
                <dl style={{ display: 'grid' }}>
                    {entries.map(([k, v], i) => (
                        <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '9px 0', borderTop: '1px solid var(--line)' }}>
                            <span style={{ width: 9, height: 9, flex: '0 0 9px', borderRadius: 3, background: COST_COLOR[i % COST_COLOR.length] }} />
                            <dt style={{ flex: 1, fontSize: 12.5 }}>{COST_LABEL[k] || k}</dt>
                            <dd className="mono" style={{ margin: 0, fontSize: 12.5, fontWeight: 500 }}>{money(v)}</dd>
                        </div>
                    ))}
                </dl>
            </section>

            {decision.assumptions?.length > 0 && (
                <section style={{ padding: 13, border: '1px solid var(--line)', borderRadius: 11, background: 'var(--soft)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: 12.5, fontWeight: 600 }}>
                        <Icon name="info" size={16} color="var(--subtle)" />Giả định chi phí
                    </div>
                    <ul style={{ margin: '8px 0 0', paddingLeft: 24, display: 'grid', gap: 4, fontSize: 12, lineHeight: 1.5, color: 'var(--dim)', listStyle: 'disc' }}>
                        {decision.assumptions.map((a, i) => <li key={i}>{a}</li>)}
                    </ul>
                    {Object.keys(fresh).length > 0 && (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginTop: 11, paddingTop: 11, borderTop: '1px solid var(--line)' }}>
                            {Object.entries(fresh).map(([k, v]) => (
                                <span key={k} className="mono" style={{ padding: '3px 8px', border: '1px solid var(--line)', borderRadius: 6, background: 'var(--surface)', fontSize: 10.5, color: 'var(--subtle)' }}>
                                    {COST_LABEL[k] || k} · {new Date(v).toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                                </span>
                            ))}
                        </div>
                    )}
                </section>
            )}
        </div>
    );
}

function Risks({ decision, onAction, loadingAction }) {
    const risks = decision?.risks || [];
    const groups = { high: [], medium: [], low: [] };
    risks.forEach((r) => (groups[r.severity] || groups.medium).push(r));
    const blocking = decision?.blocking_reasons || [];

    if (risks.length === 0 && blocking.length === 0 && !decision?.assumptions?.length) {
        return <Empty text="Không có rủi ro nào được ghi nhận." />;
    }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {blocking.length > 0 && (
                <section>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 9 }}>
                        <Icon name="block" size={18} color="var(--dgr)" />
                        <h3 style={{ fontSize: 13.5, fontWeight: 600 }}>Chưa thể khuyến nghị ({blocking.length})</h3>
                    </div>
                    <div style={{ display: 'grid', gap: 8 }}>
                        {blocking.map((r, i) => (
                            <div key={i} style={{ padding: 13, border: '1px solid var(--dgr-line)', borderRadius: 12, background: 'var(--dgr-soft)', fontSize: 12.5, lineHeight: 1.55, fontWeight: 500 }}>{r}</div>
                        ))}
                    </div>
                </section>
            )}

            {['high', 'medium', 'low'].map((sev) => {
                const items = groups[sev];
                if (!items.length) return null;
                const c = SEV[sev];
                return (
                    <section key={sev}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 9 }}>
                            <Icon name={c.icon} size={18} color={c.color} />
                            <h3 style={{ fontSize: 13.5, fontWeight: 600, color: sev === 'low' ? 'var(--dim)' : 'var(--text)' }}>{c.label} ({items.length})</h3>
                        </div>
                        <div style={{ display: 'grid', gap: 8 }}>
                            {items.map((r, i) => (
                                <div key={i} style={{ padding: '12px 13px', border: `1px solid ${c.line}`, borderRadius: 12, background: c.soft }}>
                                    <div style={{ fontSize: 12.5, lineHeight: 1.55, fontWeight: 500 }}>{r.message}</div>
                                    {r.recommendation && <div style={{ marginTop: 5, fontSize: 12, lineHeight: 1.5, color: 'var(--dim)' }}>{r.recommendation}</div>}
                                    {r.suggested_action && onAction && (
                                        <button type="button" disabled={!!loadingAction} onClick={() => onAction(r.suggested_action, r.target_day, r.target_place_id)} style={{ marginTop: 9, display: 'inline-flex', alignItems: 'center', gap: 5, padding: '6px 11px', borderRadius: 8, background: 'var(--pri)', color: 'var(--on-pri)', fontSize: 11.5, fontWeight: 600 }}>
                                            <Icon name="auto_fix_high" size={14} />{r.suggested_action === 'optimize_day' ? `Tối ưu ngày ${r.target_day}` : 'Thay địa điểm'}
                                        </button>
                                    )}
                                </div>
                            ))}
                        </div>
                    </section>
                );
            })}

            {decision?.assumptions?.length > 0 && (
                <section style={{ padding: 13, border: '1px dashed var(--line-2)', borderRadius: 11 }}>
                    <div style={eyebrow}>Mình đang giả định</div>
                    <ul style={{ margin: '8px 0 0', paddingLeft: 18, display: 'grid', gap: 4, fontSize: 12, lineHeight: 1.5, color: 'var(--dim)', listStyle: 'disc' }}>
                        {decision.assumptions.map((a, i) => <li key={i}>{a}</li>)}
                    </ul>
                </section>
            )}
        </div>
    );
}

const Empty = ({ text }) => <div style={{ padding: '32px 16px', textAlign: 'center', fontSize: 13, color: 'var(--subtle)' }}>{text}</div>;

export default function Workspace({
    workspace, sessionId, onSavePlan, savingPlan, onTripAction, loadingAction, workspaceError, isLoading, onToggleCollapse, actionDiff,
    tab, onTab, editing, onEdit, onCancelEdit,
}) {
    const setTab = onTab;
    const plan = workspace?.plan;
    const decision = workspace?.decision;

    const st = STATUS[decision?.decision_status] || STATUS.insufficient_data;
    const bars = CONFIDENCE_BARS[decision?.confidence] ?? 1;
    const todo = (decision?.blocking_reasons?.length || 0) + (decision?.risks?.filter((r) => r.severity === 'high').length || 0);

    const title = plan?.destination
        ? `${plan.destination}${plan.days ? ` · ${plan.days}N${plan.nights ?? Math.max(plan.days - 1, 0)}Đ` : ''}`
        : 'Kế hoạch chuyến đi';

    return (
        <aside data-ws="1" style={{ display: 'flex', flexDirection: 'column', background: 'var(--surface)', height: '100%', minWidth: 0 }}>
            <header style={{ padding: '16px 20px 14px', borderBottom: '1px solid var(--line)', background: 'var(--soft)' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
                    <div style={{ minWidth: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, ...eyebrow }}>
                            <Icon name="dashboard_customize" size={14} />Không gian quyết định
                        </div>
                        <h2 style={{ margin: '4px 0 0', fontSize: 21, lineHeight: 1.2, fontWeight: 700, letterSpacing: '-.02em' }}>{title}</h2>
                    </div>
                    <button type="button" onClick={onToggleCollapse} title="Thu gọn" style={{ display: 'grid', placeItems: 'center', width: 30, height: 30, borderRadius: 8, color: 'var(--subtle)' }}>
                        <Icon name="right_panel_close" size={18} />
                    </button>
                </div>
                {plan && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginTop: 11 }}>
                        {(plan.origin || plan.destination) && <span style={chip}><Icon name="flight_takeoff" size={14} color="var(--subtle)" />{plan.origin || '—'} → {plan.destination || '—'}</span>}
                        {plan.departure_date && <span style={chip}><Icon name="date_range" size={14} color="var(--subtle)" />{plan.departure_date}{plan.return_date ? ` – ${plan.return_date}` : ''}</span>}
                        <span style={chip}><Icon name="group" size={14} color="var(--subtle)" />{plan.travelers || 1} người</span>
                        {plan.budget_total && <span style={chip}><Icon name="account_balance_wallet" size={14} color="var(--subtle)" /><span className="mono" style={{ fontSize: 11 }}>{money(plan.budget_total)}</span></span>}
                    </div>
                )}
            </header>

            {workspaceError && (
                <div style={{ margin: '14px 20px 0', padding: '10px 13px', border: '1px solid var(--dgr-line)', borderRadius: 10, background: 'var(--dgr-soft)', fontSize: 12.5, color: 'var(--dgr)' }}>{workspaceError}</div>
            )}

            {isLoading && (
                <div style={{ display: 'grid', gap: 10, padding: 20 }}>
                    <div className="skeleton" style={{ height: 90 }} />
                    <div className="skeleton" style={{ height: 44 }} />
                    <div className="skeleton" style={{ height: 160 }} />
                </div>
            )}

            {!isLoading && !plan && (
                <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 14, padding: '28px 24px' }}>
                    <div style={{ width: 44, height: 44, display: 'grid', placeItems: 'center', border: '1px solid var(--line)', borderRadius: 13, background: 'var(--soft)', color: 'var(--pri)' }}>
                        <Icon name="map" size={22} />
                    </div>
                    <div>
                        <h3 style={{ fontSize: 16, fontWeight: 600, letterSpacing: '-.01em' }}>Chưa có gì để quyết định</h3>
                        <p style={{ margin: '6px 0 0', fontSize: 13, lineHeight: 1.6, color: 'var(--dim)' }}>Gửi một yêu cầu ở khung chat. Kết luận, chi phí, lịch trình và rủi ro sẽ xuất hiện ở đây.</p>
                    </div>
                    <div style={{ display: 'grid', gap: 7, padding: 13, border: '1px dashed var(--line-2)', borderRadius: 11, background: 'var(--soft)' }}>
                        <div style={eyebrow}>Mình cần biết</div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, color: 'var(--dim)' }}><Icon name="place" size={15} color="var(--pri)" />Điểm đi, điểm đến và ngày đi</div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, color: 'var(--dim)' }}><Icon name="payments" size={15} color="var(--pri)" />Ngân sách và số người</div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, color: 'var(--dim)' }}><Icon name="favorite" size={15} color="var(--pri)" />Sở thích và mức di chuyển</div>
                    </div>
                </div>
            )}

            {!isLoading && plan && (
                <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
                    {decision && (
                        <div style={{ padding: '16px 20px 0' }}>
                            <div style={{ border: `1px solid ${st.line}`, borderRadius: 14, background: 'var(--surface)', overflow: 'hidden', boxShadow: '0 1px 2px rgb(22 29 28 / .05)' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '9px 15px', background: st.soft, borderBottom: `1px solid ${st.line}` }}>
                                    <Icon name={st.icon} size={17} color={st.color} />
                                    <span style={{ flex: 1, fontSize: 12, fontWeight: 600, color: st.color }}>{st.label}</span>
                                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 11, fontWeight: 500, color: st.color }}>
                                        Tin cậy
                                        <span style={{ display: 'inline-flex', gap: 2, marginLeft: 2 }}>
                                            {[0, 1, 2].map((i) => <span key={i} style={{ width: 12, height: 4, borderRadius: 2, background: i < bars ? st.color : st.line }} />)}
                                        </span>
                                    </span>
                                </div>
                                <div style={{ padding: 15 }}>
                                    <p style={{ fontSize: 15.5, lineHeight: 1.45, fontWeight: 600, letterSpacing: '-.01em' }}>{verdictSentence(decision)}</p>
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,minmax(0,1fr))', gap: 2, margin: '14px 0', padding: '11px 0', borderTop: '1px solid var(--line)', borderBottom: '1px solid var(--line)' }}>
                                        <MiniStat label="Mỗi người" value={money(decision.total_cost_per_person)} />
                                        <MiniStat
                                            label="So ngân sách"
                                            value={decision.budget_delta == null ? '—' : money(Math.abs(decision.budget_delta))}
                                            color={decision.budget_delta == null ? undefined : decision.budget_delta < 0 ? 'var(--ok)' : 'var(--dgr)'}
                                            icon={decision.budget_delta == null ? null : decision.budget_delta < 0 ? 'arrow_downward' : 'arrow_upward'}
                                        />
                                        <MiniStat label="Cần xử lý" value={todo ? `${todo} việc` : 'Không'} color={todo ? 'var(--warn)' : 'var(--ok)'} />
                                    </div>
                                    <div style={{ display: 'flex', gap: 8 }}>
                                        <button type="button" onClick={() => setTab('itinerary')} style={{ flex: 1, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 7, minHeight: 38, borderRadius: 9, background: 'var(--pri)', color: 'var(--on-pri)', fontSize: 13, fontWeight: 600 }}>
                                            <Icon name="map" size={17} />Xem lịch trình
                                        </button>
                                        {todo > 0 && (
                                            <button type="button" onClick={() => setTab('risk')} style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 6, minHeight: 38, padding: '0 13px', border: '1px solid var(--line)', borderRadius: 9, fontSize: 13, fontWeight: 600, color: 'var(--dim)' }}>Xem lý do</button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    <div style={{ display: 'flex', gap: 2, padding: decision ? '14px 20px 0' : '4px 20px 0', borderBottom: '1px solid var(--line)', overflowX: 'auto' }}>
                        {[['overview', 'Tổng quan'], ['itinerary', 'Lịch trình'], ['cost', 'Chi phí'], ['risk', 'Rủi ro']].map(([id, label]) => (
                            <button key={id} type="button" onClick={() => setTab(id)} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '9px 12px', borderBottom: `2px solid ${tab === id ? 'var(--pri)' : 'transparent'}`, fontSize: 12.5, fontWeight: 600, color: tab === id ? 'var(--text)' : 'var(--dim)', whiteSpace: 'nowrap' }}>
                                {label}
                                {id === 'risk' && (decision?.risks?.length || decision?.blocking_reasons?.length) ? (
                                    <span className="mono" style={{ display: 'inline-grid', placeItems: 'center', minWidth: 17, height: 17, padding: '0 4px', borderRadius: 999, background: 'var(--dgr-soft)', color: 'var(--dgr)', fontSize: 10, fontWeight: 700 }}>
                                        {(decision?.risks?.length || 0) + (decision?.blocking_reasons?.length || 0)}
                                    </span>
                                ) : null}
                            </button>
                        ))}
                    </div>

                    <div style={{ flex: 1, minHeight: 0, overflowY: 'auto', padding: '18px 20px 22px' }}>
                        {tab === 'overview' && <Overview workspace={workspace} decision={decision} plan={plan} editing={editing} onEdit={onEdit} onCancelEdit={onCancelEdit} onSavePlan={onSavePlan} savingPlan={savingPlan} />}
                        {tab === 'itinerary' && <Itinerary decision={decision} onAction={onTripAction} loadingAction={loadingAction} diff={actionDiff} />}
                        {tab === 'cost' && <Cost decision={decision} />}
                        {tab === 'risk' && <Risks decision={decision} onAction={onTripAction} loadingAction={loadingAction} />}
                    </div>

                    <footer data-wsfooter="1" style={{ display: 'flex', gap: 8, padding: '12px 20px', borderTop: '1px solid var(--line)', background: 'var(--soft)' }}>
                        {sessionId && <a href={`/api/v1/trips/${sessionId}/export.md`} style={footBtn} title="Xuất Markdown"><Icon name="download" size={18} /></a>}
                        <button type="button" onClick={() => window.print()} style={footBtn} title="In PDF"><Icon name="print" size={18} /></button>
                        {decision?.decision_status === 'recommended' && decision?.booking_links?.[0] ? (
                            <a href={decision.booking_links[0]} target="_blank" rel="noreferrer" style={{ ...footBtn, flex: 1, gap: 7, color: 'var(--pri)', borderColor: 'var(--pri-line)', fontSize: 13, fontWeight: 600 }}>
                                Mở trang đặt chỗ<Icon name="open_in_new" size={16} />
                            </a>
                        ) : (
                            <span style={{ ...footBtn, flex: 1, color: 'var(--subtle)', fontSize: 12.5, fontWeight: 500, cursor: 'default' }}>
                                {decision ? 'Chưa sẵn sàng đặt chỗ' : 'Chưa có kết quả'}
                            </span>
                        )}
                    </footer>
                </div>
            )}
        </aside>
    );
}

function MiniStat({ label, value, color, icon }) {
    return (
        <div>
            <div style={eyebrow}>{label}</div>
            <div className="mono" style={{ marginTop: 3, display: 'inline-flex', alignItems: 'center', gap: 3, fontSize: 14, fontWeight: 500, color: color || 'var(--text)' }}>
                {icon && <Icon name={icon} size={15} />}{value}
            </div>
        </div>
    );
}

function verdictSentence(d) {
    const cur = money(d.total_cost);
    if (d.decision_status === 'recommended') {
        const opt = OPTION[d.recommended_option] || d.recommended_option;
        const b = BUDGET[d.budget_status]?.label?.toLowerCase() || '';
        return `Đi được với ${cur} theo phương án ${opt}${b ? ` — ${b}` : ''}.`;
    }
    if (d.decision_status === 'needs_revision') {
        return `Đi được với khoảng ${cur}, nhưng cần xử lý ${(d.blocking_reasons?.length || 0) || 'vài'} điểm trước khi đặt chỗ.`;
    }
    return d.blocking_reasons?.[0] || 'Chưa đủ dữ liệu đã xác minh để đưa ra khuyến nghị.';
}

const footBtn = { display: 'grid', placeItems: 'center', minWidth: 38, height: 38, padding: '0 12px', border: '1px solid var(--line)', borderRadius: 9, background: 'var(--surface)', color: 'var(--dim)' };
