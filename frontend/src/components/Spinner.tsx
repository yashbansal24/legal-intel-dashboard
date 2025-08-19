// frontend/src/components/Spinner.tsx
export default function Spinner({ label = "Loading..." }: { label?: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 0" }}>
      <svg
        width="18"
        height="18"
        viewBox="0 0 50 50"
        role="img"
        aria-label={label}
        style={{ color: "rgba(0,0,0,.8)" }}
      >
        <circle
          cx="25" cy="25" r="20"
          fill="none"
          stroke="currentColor"
          strokeWidth="5"
          strokeOpacity="0.2"
        />
        <path fill="currentColor" d="M25 5a20 20 0 0 1 0 40a20 20 0 0 1 0-40">
          <animateTransform
            attributeName="transform"
            type="rotate"
            from="0 25 25"
            to="360 25 25"
            dur="0.7s"
            repeatCount="indefinite"
          />
        </path>
      </svg>
      <span>{label}</span>
    </div>
  );
}
