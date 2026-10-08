/** A placeholder block shown while a page loads (never a spinner). */
export function Skeleton({ className = "" }: { className?: string }) {
  return <span aria-hidden="true" className={`block animate-pulse bg-line/70 motion-reduce:animate-none ${className}`} />;
}

/** Wraps a loading layout so screen readers hear one "Loading" instead of shapes. */
export function LoadingRegion({ label, children, className = "" }: { label: string; children: React.ReactNode; className?: string }) {
  return (
    <div role="status" aria-live="polite" aria-busy="true" className={className}>
      <span className="sr-only">{label}</span>
      {children}
    </div>
  );
}
