/** Only inside a pressed button: pages load with skeletons, never spinners. */
export function Spinner({ className = "" }: { className?: string }) {
  return (
    <span
      aria-hidden="true"
      className={`inline-block h-4 w-4 animate-spin border-2 border-current border-r-transparent motion-reduce:animate-none ${className}`}
    />
  );
}
