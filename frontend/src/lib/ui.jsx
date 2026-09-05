export function Icon({ name, size = 18, color, style }) {
    return (
        <span className="ms" style={{ fontSize: size, color, ...style }}>
            {name}
        </span>
    );
}
