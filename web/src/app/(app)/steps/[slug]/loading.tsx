import { LoadingRegion, Skeleton } from "@/components/skeleton";

export default function Loading() {
  return (
    <LoadingRegion label="Loading step" className="mx-auto grid max-w-6xl gap-10 lg:grid-cols-[minmax(0,1fr)_340px]">
      <div>
        <Skeleton className="h-3 w-56" />
        <Skeleton className="mt-5 h-12 w-3/4" />
        <Skeleton className="mt-4 h-3 w-64" />
        <div className="mt-10 max-w-[68ch] space-y-3">
          {Array.from({ length: 9 }, (_, i) => (
            <Skeleton key={i} className={`h-4 ${i % 4 === 3 ? "w-2/3" : "w-full"}`} />
          ))}
        </div>
      </div>
      <div className="hidden border-2 border-line p-6 lg:block">
        <Skeleton className="h-3 w-28" />
        <Skeleton className="mt-4 h-4 w-full" />
        <Skeleton className="mt-2 h-4 w-4/5" />
        <Skeleton className="mt-6 h-12 w-full" />
      </div>
    </LoadingRegion>
  );
}
