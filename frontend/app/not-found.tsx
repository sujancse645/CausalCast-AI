import Link from "next/link";
export default function NotFound() {
  return (
    <div className="panel mx-auto max-w-lg p-8 text-center">
      <p className="text-blue-400">404</p>
      <h2 className="mt-2 text-xl font-semibold">Page not found</h2>
      <Link href="/dashboard" className="mt-5 inline-block text-blue-400">
        Return to dashboard
      </Link>
    </div>
  );
}
