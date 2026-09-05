import { useState } from 'react';

const field = { display: 'grid', gap: 5, fontSize: 11.5, fontWeight: 600, color: 'var(--dim)' };
const input = { minHeight: 36, padding: '0 10px', border: '1px solid var(--line)', borderRadius: 8, background: 'var(--surface)', fontSize: 12.5, outline: 0 };

export default function PlanEditor({ plan, onSave, onCancel, saving }) {
    const [form, setForm] = useState({
        origin: plan?.origin || '',
        destination: plan?.destination || '',
        departure_date: plan?.departure_date || '',
        return_date: plan?.return_date || '',
        days: plan?.days || '',
        travelers: plan?.travelers || 1,
        budget_total: plan?.budget_total || '',
        preferences: (plan?.preferences || []).join(', '),
        comfort_level: plan?.comfort_level || 'medium',
        priority: plan?.priority || 'cheapest',
    });
    const set = (k, v) => setForm((c) => ({ ...c, [k]: v }));

    const submit = (e) => {
        e.preventDefault();
        onSave({
            ...form,
            days: form.days ? Number(form.days) : null,
            travelers: Number(form.travelers),
            budget_total: form.budget_total ? Number(form.budget_total) : null,
            preferences: form.preferences.split(',').map((v) => v.trim()).filter(Boolean),
            departure_date: form.departure_date || null,
            return_date: form.return_date || null,
        });
    };

    return (
        <form onSubmit={submit} style={{ display: 'grid', gap: 10, padding: 15, border: '1px solid var(--line)', borderRadius: 13, background: 'var(--soft)' }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, letterSpacing: '-.01em' }}>Chỉnh kế hoạch</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                <label style={field}>Điểm đi<input style={input} value={form.origin} onChange={(e) => set('origin', e.target.value)} /></label>
                <label style={field}>Điểm đến<input style={input} required value={form.destination} onChange={(e) => set('destination', e.target.value)} /></label>
                <label style={field}>Ngày đi<input style={input} type="date" value={form.departure_date} onChange={(e) => set('departure_date', e.target.value)} /></label>
                <label style={field}>Ngày về<input style={input} type="date" value={form.return_date} onChange={(e) => set('return_date', e.target.value)} /></label>
                <label style={field}>Số ngày<input style={input} type="number" min="1" value={form.days} onChange={(e) => set('days', e.target.value)} /></label>
                <label style={field}>Số người<input style={input} type="number" min="1" value={form.travelers} onChange={(e) => set('travelers', e.target.value)} /></label>
                <label style={field}>Ngân sách tổng<input style={input} type="number" min="0" value={form.budget_total} onChange={(e) => set('budget_total', e.target.value)} /></label>
                <label style={field}>Mức thoải mái
                    <select style={input} value={form.comfort_level} onChange={(e) => set('comfort_level', e.target.value)}>
                        <option value="budget">Tiết kiệm</option>
                        <option value="medium">Cân bằng</option>
                        <option value="comfortable">Thoải mái</option>
                    </select>
                </label>
            </div>
            <label style={field}>Sở thích<input style={input} required value={form.preferences} onChange={(e) => set('preferences', e.target.value)} placeholder="biển, ăn ngon, không quá mệt" /></label>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
                <button type="button" onClick={onCancel} style={{ padding: '0 13px', minHeight: 34, border: '1px solid var(--line)', borderRadius: 8, fontSize: 12.5, fontWeight: 600, color: 'var(--dim)' }}>Huỷ</button>
                <button type="submit" disabled={saving} style={{ padding: '0 13px', minHeight: 34, borderRadius: 8, background: 'var(--pri)', color: 'var(--on-pri)', fontSize: 12.5, fontWeight: 600 }}>{saving ? 'Đang lưu…' : 'Lưu thay đổi'}</button>
            </div>
        </form>
    );
}
