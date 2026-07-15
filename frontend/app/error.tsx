"use client";
export default function ErrorPage({
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <div className="panel mx-auto max-w-lg p-8 text-center">
      <h2 className="text-xl font-semibold">Something went wrong</h2>
      <p className="muted mt-2">
        The interface could not complete this request.
      </p>
      <button onClick={reset} className="mt-5 rounded-lg bg-blue-600 px-4 py-2">
        Try again
      </button>
    </div>
  );
}
