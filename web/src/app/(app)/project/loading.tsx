import { LoadingRegion, Skeleton } from "@/components/skeleton";

export default function Loading() {
  return (
    <LoadingRegion label="Loading your project" className="mx-auto max-w-4xl">
      <Skeleton className="h-3 w-28" />
      <Skeleton className="mt-4 h-11 w-1/2" />
      <Skeleton className="mt-4 h-4 w-2/3" />
      <div className="mt-10 grid gap-8 lg:grid-cols-[1.3fr_1fr]">
        <div className="space-y-6">
          {Array.from({ length: 4 }, (_, i) => (
            <div key={i}>
              <Skeleton className="h-3 w-32" />
              <Skeleton className="mt-2 h-12 w-full" />
            </div>
          ))}
        </div>
        <Skeleton className="h-64 w-full" />
      </div>
    </LoadingRegion>
  );
}
