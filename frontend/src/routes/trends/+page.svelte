<script lang="ts">
	import { getTimeSeries } from "../data.remote";
	import * as Card from "$lib/components/ui/card/index.js";
	import AreaChart from "$lib/components/AreaChart.svelte";
	import BarChart from "$lib/components/BarChart.svelte";

	const { byYear, activeByYear } = await getTimeSeries();

	const cumulativeData = byYear.map((d) => ({ label: d.year, value: d.cumulative }));
	const createdData = byYear.map((d) => ({ label: d.year, value: d.created }));
</script>

<div class="p-6 w-full space-y-6 overflow-hidden">
	<div>
		<h1 class="text-3xl font-bold">Trends</h1>
		<p class="text-muted-foreground">GitHub adoption at UVM over time</p>
	</div>

	<Card.Root>
		<Card.Header>
			<Card.Title>Cumulative Repositories</Card.Title>
		</Card.Header>
		<Card.Content>
			<AreaChart data={cumulativeData} color="#154734" />
		</Card.Content>
	</Card.Root>

	<Card.Root>
		<Card.Header>
			<Card.Title>New Repositories per Year</Card.Title>
		</Card.Header>
		<Card.Content>
			<BarChart data={createdData} color="#154734" />
		</Card.Content>
	</Card.Root>
</div>
