interface SpinnerProps {
  label?: string;
}

export function Spinner({ label = "Loading" }: SpinnerProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex items-center justify-center gap-3 py-12 text-bean-700"
    >
      <span
        aria-hidden="true"
        className="inline-block h-5 w-5 animate-spin rounded-full border-2 border-bean-500 border-t-transparent"
      />
      <span>{label}</span>
    </div>
  );
}
