<script lang="ts">
	import { pie, arc } from "d3-shape";

	let {
		data,
		height = 220
	}: {
		data: { label: string; value: number }[];
		height?: number;
	} = $props();

	let width = height;

	const COLORS = [
		"#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
		"#06b6d4", "#f97316", "#84cc16", "#ec4899", "#6366f1",
		"#14b8a6", "#eab308", "#64748b", "#a855f7", "#22c55e"
	];

	let radius = $derived(Math.min(width, height) / 2);
	let innerRadius = $derived(radius * 0.55);

	const pieGen = pie<{ label: string; value: number }>()
		.value((d) => d.value)
		.sort(null);

	let arcGen = $derived(
		arc<{ startAngle: number; endAngle: number }>()
			.innerRadius(innerRadius)
			.outerRadius(radius - 4)
	);

	let arcs = $derived(pieGen(data));
</script>

<div class="flex flex-col items-center gap-3 w-full overflow-hidden">
	<svg width={width} {height} viewBox="{-width / 2} {-height / 2} {width} {height}" class="shrink-0">
		{#each arcs as a, i}
			<path
				d={arcGen(a) ?? ""}
				fill={COLORS[i % COLORS.length]}
				stroke="white"
				stroke-width="2"
			>
				<title>{a.data.label}: {a.data.value}</title>
			</path>
		{/each}
	</svg>
	<div class="flex flex-wrap gap-x-4 gap-y-1 text-xs justify-center">
		{#each data as item, i}
			<div class="flex items-center gap-1.5">
				<span
					class="inline-block w-2.5 h-2.5 rounded-sm shrink-0"
					style="background:{COLORS[i % COLORS.length]}"
				></span>
				<span class="text-muted-foreground">{item.label}</span>
				<span class="font-medium">{item.value}</span>
			</div>
		{/each}
	</div>
</div>
