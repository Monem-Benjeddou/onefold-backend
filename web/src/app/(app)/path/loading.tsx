import { LoadingRegion, Skeleton } from "@/components/skeleton";

export default function Loading() {
  return (
    <LoadingRegion label="Loading the path" className="mx-auto max-w-4xl">
      <Skeleton className="h-3 w-24" />
      <Skeleton className="mt-4 h-11 w-3/4" />
      <Skeleton className="mt-4 h-4 w-1/2" />
      <Skeleton className="mt-8 h-2.5 w-full" />
      {Array.from({ length: 3 }, (_, i) => (
        <div key={i} className="mt-12">
          <Skeleton className="h-7 w-48" />
          <Skeleton className="mt-5 h-5 w-full" />
          <Skeleton className="mt-5 h-5 w-full" />
        </div>
      ))}
    </LoadingRegion>
  );
}
