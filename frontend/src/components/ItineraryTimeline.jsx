
import React from 'react';

const TrustBadge = ({ status }) => {
  const config = {
    verified: { label: 'Đã xác thực', icon: '✓', className: 'verified' },
    estimated: { label: 'Ước tính', icon: '⚠', className: 'estimated' },
    unverified: { label: 'Chưa kiểm chứng', icon: '?', className: 'unverified' },
    fixture: { label: 'Dữ liệu Test', icon: '🧪', className: 'estimated' }
  };

  const { label, icon, className } = config[status] || config.unverified;

  return (
    <div className={`trust-badge ${className}`}>
      <span>{icon}</span>
      <span>{label}</span>
    </div>
  );
};

const PlaceCard = ({ place, currency = 'VND', onAction, loadingAction }) => {
  const money = (v) =>
    v == null || v === 0 ? null : `${new Intl.NumberFormat('vi-VN').format(v)} ${currency}`;

  return (
    <div className="place-card">
      <div className="place-card-header">
        <div>
          <span className="place-category">{place.category}</span>
          <h3 className="place-title">{place.title}</h3>
          <div className="place-area">
            <span>📍</span> {place.area || place.title}
          </div>
        </div>
        <TrustBadge status={place.confidence || 'unverified'} />
      </div>

      <div className="place-details">
        <div className="detail-item">
          <span className="detail-label">Thời gian</span>
          <span className="detail-value">{place.estimated_visit_minutes} phút</span>
        </div>
        {money(place.estimated_cost) && (
          <div className="detail-item">
            <span className="detail-label">Dự kiến chi</span>
            <span className="detail-value">{money(place.estimated_cost)}</span>
          </div>
        )}
      </div>

      <div className="place-footer">
        {place.maps_url && (
          <a href={place.maps_url} target="_blank" rel="noopener noreferrer" className="maps-link">
            Mở Maps ↗
          </a>
        )}
        {onAction && place.category && (
          <button 
            className="action-btn no-print" 
            onClick={() => onAction('replace_place', null, place.place_id)}
            disabled={loadingAction != null}
            style={{ marginLeft: 'auto', fontSize: '0.85em', padding: '4px 8px' }}
          >
            {loadingAction?.action === 'replace_place' && loadingAction?.target === place.place_id 
              ? 'Đang tìm...' : 'Thay địa điểm'}
          </button>
        )}
      </div>
    </div>
  );
};

const RouteLegCard = ({ leg }) => {
  const isUnverified = leg.confidence === 'unverified';
  
  return (
    <div className="route-leg">
      <div className="route-leg-content">
        <div className="route-info">
          <div className="route-mode-icon">
            {leg.mode === 'driving' ? '🚗' : leg.mode === 'transit' ? '🚌' : '🚶'}
          </div>
          <div>
            {!isUnverified && (
              <div className="route-metrics">
                <span>{leg.distance_km}km</span>
                <span>•</span>
                <span>{leg.duration_minutes} phút</span>
              </div>
            )}
            {isUnverified && leg.directions_url && (
              <a href={leg.directions_url} target="_blank" rel="noopener noreferrer" className="route-search-link">Tìm trên Maps</a>
            )}
            {isUnverified && !leg.directions_url && (
              <span className="route-search-link">Chưa rõ tuyến đường</span>
            )}
          </div>
        </div>
        <TrustBadge status={leg.confidence || 'unverified'} />
      </div>
    </div>
  );
};

export default function ItineraryTimeline({ itinerary, currency = 'VND', onAction, loadingAction }) {
    if (!itinerary || itinerary.length === 0) return null;

    return (
        <section className="workspace-section itinerary-timeline" aria-label="Lịch trình theo ngày">
            <h3>Lịch trình theo ngày</h3>
            <div className="timeline-container">
                {itinerary.map((day) => (
                    <article className="timeline-day" key={day.day}>
                        <div className="timeline-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div className="day-label">
                                {day.title || `Ngày ${day.day}`}
                                {day.date && <span style={{fontSize: '0.8em', color: 'var(--color-text-muted)', marginLeft: '8px'}}>{day.date}</span>}
                            </div>
                            {onAction && day.items.length > 2 && (
                                <button 
                                    className="action-btn no-print"
                                    onClick={() => onAction('optimize_day', day.day, null)}
                                    disabled={loadingAction != null}
                                    style={{ fontSize: '0.85em', padding: '6px 12px' }}
                                >
                                    {loadingAction?.action === 'optimize_day' && loadingAction?.target === day.day 
                                        ? 'Đang tối ưu...' : 'Tối ưu ngày này'}
                                </button>
                            )}
                        </div>

                        {day.route_legs && day.route_legs.length > 0 ? (
                            // Use route_legs if available (S1-05/S1-06 structure)
                            day.route_legs.map((leg, idx) => (
                                <React.Fragment key={`leg-${idx}`}>
                                    <RouteLegCard leg={leg} />
                                    {/* The leg points to a destination. We render the place from day.items that matches the destination */}
                                    {idx < day.items.length && (
                                        <PlaceCard place={day.items[idx]} currency={currency} onAction={onAction} loadingAction={loadingAction} />
                                    )}
                                </React.Fragment>
                            ))
                        ) : (
                            // Fallback if no route_legs
                            day.items.map((item, idx) => (
                                <PlaceCard key={`item-${idx}`} place={item} currency={currency} onAction={onAction} loadingAction={loadingAction} />
                            ))
                        )}

                        {day.evidence?.length > 0 && (
                            <div className="day-warnings" style={{marginTop: '16px'}}>
                                {day.evidence.map((ev, i) => (
                                    <div className="workspace-warning" key={`ev-${day.day}-${i}`} style={{padding: '12px', background: 'var(--status-estimated-bg)', borderRadius: '8px', marginBottom: '8px'}}>
                                        <strong style={{color: 'var(--status-estimated-text)'}}>⚠️ {ev.rule}</strong>
                                        <p style={{ margin: '4px 0 0 0', fontSize: '0.9em', color: 'var(--color-text-main)' }}>
                                            Thực tế: {ev.observed_value}
                                        </p>
                                        {ev.recommendation && (
                                            <p style={{ margin: '4px 0 0 0', fontSize: '0.9em', fontStyle: 'italic', color: 'var(--color-text-muted)' }}>
                                                Gợi ý: {ev.recommendation}
                                            </p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </article>
                ))}
            </div>
        </section>
    );
}
