interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div
      role="alert"
      className="rounded-2xl bg-white p-6 text-center shadow-sm ring-1 ring-red-200"
    >
      <p className="text-sm font-medium text-red-700">Something went wrong.</p>
      <p className="mt-1 text-sm text-bean-700">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 rounded-lg bg-bean-700 px-4 py-2 text-sm font-semibold text-white hover:bg-bean-900"
        >
          Try again
        </button>
      )}
    </div>
  );
}
