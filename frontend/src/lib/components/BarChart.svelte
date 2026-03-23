<script lang="ts">
	import { scaleBand, scaleLinear } from "d3-scale";
	import { max } from "d3-array";

	let {
		data,
		horizontal = false,
		color = "#3b82f6",
		height = 300,
		formatTick
	}: {
		data: { label: string; value: number }[];
		horizontal?: boolean;
		color?: string;
		height?: number;
		formatTick?: (v: number) => string;
	} = $props();

	let containerWidth = $state(0);
	let width = $derived(containerWidth || 500);

	let margin = $derived({ top: 10, right: 16, bottom: 30, left: horizontal ? 120 : 40 });
	let innerW = $derived(width - margin.left - margin.right);
	let innerH = $derived(height - margin.top - margin.bottom);

	let bandScale = $derived(
		scaleBand<string>()
			.domain(data.map((d) => d.label))
			.range(horizontal ? [0, innerH] : [0, innerW])
			.padding(0.2)
	);

	let linearScale = $derived(
		scaleLinear()
			.domain([0, max(data, (d) => d.value) ?? 1])
			.range(horizontal ? [0, innerW] : [innerH, 0])
			.nice()
	);

	let ticks = $derived(linearScale.ticks(5));
	const fmt = (v: number) => (formatTick ? formatTick(v) : String(v));
</script>

<div bind:clientWidth={containerWidth} class="w-full">
<svg width="100%" {height} viewBox="0 0 {width} {height}">
	<g transform="translate({margin.left},{margin.top})">
		<!-- Grid lines -->
		{#each ticks as t}
			{#if horizontal}
				<line
					x1={linearScale(t)}
					x2={linearScale(t)}
					y1={0}
					y2={innerH}
					stroke="#e2e8f0"
					stroke-dasharray="3,3"
				/>
			{:else}
				<line
					x1={0}
					x2={innerW}
					y1={linearScale(t)}
					y2={linearScale(t)}
					stroke="#e2e8f0"
					stroke-dasharray="3,3"
				/>
			{/if}
		{/each}

		<!-- Bars -->
		{#each data as d}
			{#if horizontal}
				<rect
					x={0}
					y={bandScale(d.label) ?? 0}
					width={linearScale(d.value)}
					height={bandScale.bandwidth()}
					fill={color}
					rx={4}
				>
					<title>{d.label}: {d.value}</title>
				</rect>
			{:else}
				<rect
					x={bandScale(d.label) ?? 0}
					y={linearScale(d.value)}
					width={bandScale.bandwidth()}
					height={innerH - linearScale(d.value)}
					fill={color}
					rx={4}
				>
					<title>{d.label}: {d.value}</title>
				</rect>
			{/if}
		{/each}

		<!-- Axes labels -->
		{#if horizontal}
			{#each data as d}
				<text
					x={-8}
					y={(bandScale(d.label) ?? 0) + bandScale.bandwidth() / 2}
					text-anchor="end"
					dominant-baseline="central"
					class="fill-muted-foreground text-xs"
				>
					{d.label}
				</text>
			{/each}
			{#each ticks as t}
				<text
					x={linearScale(t)}
					y={innerH + 20}
					text-anchor="middle"
					class="fill-muted-foreground text-xs"
				>
					{fmt(t)}
				</text>
			{/each}
		{:else}
			{#each data as d}
				<text
					x={(bandScale(d.label) ?? 0) + bandScale.bandwidth() / 2}
					y={innerH + 20}
					text-anchor="middle"
					class="fill-muted-foreground text-xs"
				>
					{d.label}
				</text>
			{/each}
			{#each ticks as t}
				<text
					x={-8}
					y={linearScale(t)}
					text-anchor="end"
					dominant-baseline="central"
					class="fill-muted-foreground text-xs"
				>
					{fmt(t)}
				</text>
			{/each}
		{/if}
	</g>
</svg>
</div>
