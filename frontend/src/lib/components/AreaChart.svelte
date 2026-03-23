<script lang="ts">
	import { scalePoint, scaleLinear } from "d3-scale";
	import { area, line, curveMonotoneX } from "d3-shape";
	import { max } from "d3-array";

	let {
		data,
		color = "#154734",
		height = 300
	}: {
		data: { label: string; value: number }[];
		color?: string;
		height?: number;
	} = $props();

	let containerWidth = $state(0);
	let width = $derived(containerWidth || 500);

	let margin = { top: 10, right: 16, bottom: 30, left: 50 };
	let innerW = $derived(width - margin.left - margin.right);
	let innerH = $derived(height - margin.top - margin.bottom);

	let xScale = $derived(
		scalePoint<string>()
			.domain(data.map((d) => d.label))
			.range([0, innerW])
	);

	let yScale = $derived(
		scaleLinear()
			.domain([0, max(data, (d) => d.value) ?? 1])
			.range([innerH, 0])
			.nice()
	);

	let ticks = $derived(yScale.ticks(5));

	let areaGenerator = $derived(
		area<{ label: string; value: number }>()
			.x((d) => xScale(d.label) ?? 0)
			.y0(innerH)
			.y1((d) => yScale(d.value))
			.curve(curveMonotoneX)
	);

	let lineGenerator = $derived(
		line<{ label: string; value: number }>()
			.x((d) => xScale(d.label) ?? 0)
			.y((d) => yScale(d.value))
			.curve(curveMonotoneX)
	);

	let areaPath = $derived(areaGenerator(data) ?? "");
	let linePath = $derived(lineGenerator(data) ?? "");
</script>

<div bind:clientWidth={containerWidth} class="w-full">
<svg width="100%" {height} viewBox="0 0 {width} {height}">
	<g transform="translate({margin.left},{margin.top})">
		<!-- Horizontal grid lines -->
		{#each ticks as t (t)}
			<line
				x1={0}
				x2={innerW}
				y1={yScale(t)}
				y2={yScale(t)}
				stroke="#e2e8f0"
				stroke-dasharray="3,3"
			/>
		{/each}

		<!-- Filled area -->
		<path d={areaPath} fill={color} opacity={0.2} />

		<!-- Line on top -->
		<path d={linePath} fill="none" stroke={color} stroke-width={2} />

		<!-- Data point circles -->
		{#each data as d (d.label)}
			<circle
				cx={xScale(d.label) ?? 0}
				cy={yScale(d.value)}
				r={3}
				fill={color}
			>
				<title>{d.label}: {d.value}</title>
			</circle>
		{/each}

		<!-- X-axis labels -->
		{#each data as d (d.label)}
			<text
				x={xScale(d.label) ?? 0}
				y={innerH + 20}
				text-anchor="middle"
				class="fill-muted-foreground text-xs"
			>
				{d.label}
			</text>
		{/each}

		<!-- Y-axis tick labels -->
		{#each ticks as t (t)}
			<text
				x={-8}
				y={yScale(t)}
				text-anchor="end"
				dominant-baseline="central"
				class="fill-muted-foreground text-xs"
			>
				{t}
			</text>
		{/each}
	</g>
</svg>
</div>
