<script lang="ts">
	import { sankey, sankeyLinkHorizontal } from 'd3-sankey';
	import type { SankeyNode as D3SankeyNode, SankeyLink as D3SankeyLink } from 'd3-sankey';

	interface SankeyNode {
		name: string;
	}

	interface SankeyLink {
		source: number;
		target: number;
		value: number;
	}

	let {
		nodes,
		links,
		width = 900,
		height = 500
	}: {
		nodes: SankeyNode[];
		links: SankeyLink[];
		width?: number;
		height?: number;
	} = $props();

	// Color palette by layer
	const sourceColors = ['#0ea5e9', '#06b6d4', '#14b8a6', '#0284c7', '#0891b2', '#0d9488'];
	const methodColors = ['#f59e0b', '#d97706', '#b45309', '#ea580c', '#e67e22', '#f97316'];
	const labelColorMap: Record<string, string> = {
		'UVM Vermont': '#22c55e',
		'Not UVM': '#ef4444',
		'UVM Mexico': '#a855f7',
		'UVM Verification': '#6b7280'
	};

	function getNodeColor(node: D3SankeyNode<SankeyNode, SankeyLink>): string {
		const depth = node.depth ?? 0;
		if (depth === 0) {
			return sourceColors[(node.index ?? 0) % sourceColors.length];
		}
		if (depth === 2 || (node.targetLinks && node.targetLinks.length > 0 && (!node.sourceLinks || node.sourceLinks.length === 0))) {
			const mapped = labelColorMap[node.name];
			if (mapped) return mapped;
			return '#6b7280';
		}
		return methodColors[(node.index ?? 0) % methodColors.length];
	}

	// Compute sankey layout reactively, deep-copying inputs to avoid mutation issues
	let layout = $derived.by(() => {
		const nodesCopy = nodes.map((n) => ({ ...n }));
		const linksCopy = links.map((l) => ({ ...l }));

		const sankeyGenerator = sankey<SankeyNode, SankeyLink>()
			.nodeWidth(20)
			.nodePadding(12)
			.extent([
				[1, 5],
				[width - 1, height - 5]
			]);

		return sankeyGenerator({
			nodes: nodesCopy,
			links: linksCopy
		});
	});

	let layoutNodes = $derived(layout.nodes);
	let layoutLinks = $derived(layout.links);
	let linkPath = sankeyLinkHorizontal();

	let hoveredLink = $state<number | null>(null);
</script>

<svg {width} {height}>
	<!-- Links -->
	<g fill="none">
		{#each layoutLinks as link, i (i)}
			{@const sourceNode = link.source as D3SankeyNode<SankeyNode, SankeyLink>}
			<path
				role="img"
				aria-label="{(link.source as D3SankeyNode<SankeyNode, SankeyLink>).name} to {(link.target as D3SankeyNode<SankeyNode, SankeyLink>).name}: {link.value}"
				d={linkPath(link as any)}
				stroke={getNodeColor(sourceNode)}
				stroke-opacity={hoveredLink === i ? 0.7 : 0.4}
				stroke-width={Math.max(1, link.width ?? 0)}
				onmouseenter={() => (hoveredLink = i)}
				onmouseleave={() => (hoveredLink = null)}
			>
				<title>
					{(link.source as D3SankeyNode<SankeyNode, SankeyLink>).name} → {(link.target as D3SankeyNode<SankeyNode, SankeyLink>).name}: {link.value}
				</title>
			</path>
		{/each}
	</g>

	<!-- Nodes -->
	<g>
		{#each layoutNodes as node (node.index)}
			<rect
				x={node.x0}
				y={node.y0}
				width={(node.x1 ?? 0) - (node.x0 ?? 0)}
				height={(node.y1 ?? 0) - (node.y0 ?? 0)}
				fill={getNodeColor(node)}
				rx={2}
			>
				<title>{node.name}: {node.value}</title>
			</rect>
		{/each}
	</g>

	<!-- Labels -->
	<g class="fill-foreground text-xs" style="font-size: 11px;">
		{#each layoutNodes as node (node.index)}
			{@const x0 = node.x0 ?? 0}
			{@const x1 = node.x1 ?? 0}
			{@const y0 = node.y0 ?? 0}
			{@const y1 = node.y1 ?? 0}
			{@const isRight = x0 > width / 2}
			<text
				x={isRight ? x0 - 6 : x1 + 6}
				y={(y0 + y1) / 2}
				text-anchor={isRight ? 'end' : 'start'}
				dominant-baseline="central"
				fill="currentColor"
			>
				{node.name} ({node.value})
			</text>
		{/each}
	</g>
</svg>
