import { useState } from 'react';

export default function PlanEditor({ plan, onSave, onCancel, saving }) {
    const [form, setForm] = useState({
        destination: plan?.destination || '',
        origin: plan?.origin || '',
        departure_date: plan?.departure_date || '',
        return_date: plan?.return_date || '',
        days: plan?.days || '',
        travelers: plan?.travelers || 1,
        budget_total: plan?.budget_total || '',
        preferences: (plan?.preferences || []).join(', '),
        comfort_level: plan?.comfort_level || 'medium',
        priority: plan?.priority || 'cheapest',
    });

    const update = (field, value) => setForm((current) => ({ ...current, [field]: value }));
    const submit = (event) => {
        event.preventDefault();
        onSave({
            ...form,
            days: form.days ? Number(form.days) : null,
            travelers: Number(form.travelers),
            budget_total: form.budget_total ? Number(form.budget_total) : null,
            preferences: form.preferences.split(',').map((value) => value.trim()).filter(Boolean),
            departure_date: form.departure_date || null,
            return_date: form.return_date || null,
        });
    };

    return (
        <form className="plan-editor" onSubmit={submit}>
            <h3>Chỉnh kế hoạch</h3>
            <div className="plan-editor-grid">
                <label>Điểm đi<input value={form.origin} onChange={(event) => update('origin', event.target.value)} /></label>
                <label>Điểm đến<input required value={form.destination} onChange={(event) => update('destination', event.target.value)} /></label>
                <label>Ngày đi<input type="date" value={form.departure_date} onChange={(event) => update('departure_date', event.target.value)} /></label>
                <label>Ngày về<input type="date" value={form.return_date} onChange={(event) => update('return_date', event.target.value)} /></label>
                <label>Số ngày<input type="number" min="1" value={form.days} onChange={(event) => update('days', event.target.value)} /></label>
                <label>Số người<input type="number" min="1" value={form.travelers} onChange={(event) => update('travelers', event.target.value)} /></label>
                <label>Ngân sách tổng<input type="number" min="1" value={form.budget_total} onChange={(event) => update('budget_total', event.target.value)} /></label>
                <label>Mức thoải mái
                    <select value={form.comfort_level} onChange={(event) => update('comfort_level', event.target.value)}>
                        <option value="budget">Tiết kiệm</option>
                        <option value="medium">Cân bằng</option>
                        <option value="comfortable">Thoải mái</option>
                    </select>
                </label>
                <label>Ưu tiên
                    <select value={form.priority} onChange={(event) => update('priority', event.target.value)}>
                        <option value="cheapest">Tiết kiệm nhất</option>
                        <option value="less_travel">Di chuyển ít</option>
                        <option value="comfortable">Thoải mái nhất</option>
                    </select>
                </label>
            </div>
            <label>Sở thích<input required value={form.preferences} onChange={(event) => update('preferences', event.target.value)} placeholder="biển, ăn ngon, không quá mệt" /></label>
            <div className="plan-editor-actions">
                <button type="button" onClick={onCancel}>Hủy</button>
                <button type="submit" disabled={saving}>{saving ? 'Đang lưu...' : 'Lưu thay đổi'}</button>
            </div>
        </form>
    );
}
