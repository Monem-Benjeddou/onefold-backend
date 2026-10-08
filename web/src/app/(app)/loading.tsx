import { LoadingRegion, Skeleton } from "@/components/skeleton";

/** Shown instantly while any app page loads. */
export default function Loading() {
  return (
    <LoadingRegion label="Loading" className="mx-auto max-w-5xl">
      <Skeleton className="h-3 w-40" />
      <Skeleton className="mt-4 h-11 w-2/3 max-w-md" />
      <div className="mt-10 grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        <div className="border-2 border-line p-6 sm:p-8">
          <Skeleton className="h-3 w-28" />
          <Skeleton className="mt-4 h-8 w-1/2" />
          <Skeleton className="mt-6 h-2.5 w-full" />
          <Skeleton className="mt-8 h-3 w-1/3" />
          <Skeleton className="mt-3 h-6 w-3/4" />
          <Skeleton className="mt-6 h-12 w-44" />
        </div>
        <div className="border border-line p-6 sm:p-8">
          {Array.from({ length: 6 }, (_, i) => (
            <Skeleton key={i} className="mt-3 h-4 w-full first:mt-0" />
          ))}
        </div>
      </div>
    </LoadingRegion>
  );
}
