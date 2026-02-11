import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">404</h1>
        <p className="text-muted-foreground mb-6">Page not found</p>
        <Link
          href="/ai-company-directory/en"
          className="text-primary hover:underline"
        >
          Go to Home
        </Link>
      </div>
    </div>
  );
}
