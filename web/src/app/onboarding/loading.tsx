import { LoadingRegion, Skeleton } from "@/components/skeleton";

export default function Loading() {
  return (
    <LoadingRegion label="Loading" className="mx-auto max-w-3xl px-4 pt-24 sm:px-6">
      <div className="grid grid-cols-4 gap-1.5">
        {Array.from({ length: 4 }, (_, i) => (
          <Skeleton key={i} className="h-1.5" />
        ))}
      </div>
      <Skeleton className="mt-12 h-3 w-24" />
      <Skeleton className="mt-4 h-12 w-4/5" />
      <Skeleton className="mt-8 h-28 w-full" />
    </LoadingRegion>
  );
}
