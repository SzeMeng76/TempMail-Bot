export function MessageSkeleton() {
	return (
		<div className="divide-y divide-white/60 dark:divide-white/10">
			{Array.from({ length: 4 }).map((_, i) => (
				<div key={i} className="px-4 py-3 flex items-start gap-3 animate-pulse">
					<div className="mt-1 w-2 h-2 rounded-full bg-slate-200 dark:bg-white/10 shrink-0" />
					<div className="flex-1 space-y-2">
						<div className="flex items-center justify-between gap-2">
							<div className="h-3 w-28 rounded bg-slate-200 dark:bg-white/10" />
							<div className="h-3 w-10 rounded bg-slate-200 dark:bg-white/10" />
						</div>
						<div className="h-3 w-40 rounded bg-slate-200 dark:bg-white/10" />
						<div className="h-2.5 w-56 rounded bg-slate-100 dark:bg-white/5" />
					</div>
				</div>
			))}
		</div>
	);
}
