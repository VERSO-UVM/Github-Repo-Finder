<script lang="ts">
	import * as Card from "$lib/components/ui/card/index.js";
	import StatCard from "$lib/components/StatCard.svelte";
	import DoughnutChart from "$lib/components/DoughnutChart.svelte";
	import BarChart from "$lib/components/BarChart.svelte";
	import RepoTable from "$lib/components/RepoTable.svelte";
	import { getSummary, getLangCounts, getLicenseCounts, getFeatureStats, getStarBuckets, getTopRepos } from "./data.remote";

	const summary = await getSummary();
	const langCounts = await getLangCounts();
	const licenseCounts = await getLicenseCounts();
	const featureStats = await getFeatureStats();
	const starBuckets = await getStarBuckets();
	const repos = await getTopRepos();

	const langData = Object.entries(langCounts).map(([label, value]) => ({ label, value }));
	const licenseData = Object.entries(licenseCounts).map(([label, value]) => ({ label, value }));
	const featureBarData = featureStats.map((f) => ({ label: f.label, value: f.pct }));
	const starData = Object.entries(starBuckets).map(([label, value]) => ({ label, value }));
</script>

<div class="p-6 w-full space-y-6 overflow-hidden">
	<div>
		<h1 class="text-3xl font-bold">{summary.acronym} Open-Source Repository Dashboard</h1>
		<p class="text-muted-foreground">Data from GitHub scraping via repofinder</p>
	</div>

	<!-- Stat cards -->
	<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
		<StatCard icon="📦" value={summary.total.toLocaleString()} label="Repositories" />
		<StatCard icon="⭐" value={summary.totalStars.toLocaleString()} label="Total Stars" />
		<StatCard icon="🍴" value={summary.totalForks.toLocaleString()} label="Total Forks" />
		<StatCard icon="💻" value={summary.uniqueLangs.toLocaleString()} label="Languages" />
	</div>

	<!-- Charts -->
	<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
		<Card.Root>
			<Card.Header>
				<Card.Title>Language Distribution</Card.Title>
			</Card.Header>
			<Card.Content>
				<DoughnutChart data={langData} />
			</Card.Content>
		</Card.Root>

		<Card.Root>
			<Card.Header>
				<Card.Title>License Distribution</Card.Title>
			</Card.Header>
			<Card.Content>
				<DoughnutChart data={licenseData} />
			</Card.Content>
		</Card.Root>

		<Card.Root>
			<Card.Header>
				<Card.Title>Community Features Adoption</Card.Title>
			</Card.Header>
			<Card.Content>
				<BarChart
					data={featureBarData}
					horizontal={true}
					color="#10b981"
					height={260}
					formatTick={(v) => v + "%"}
				/>
			</Card.Content>
		</Card.Root>
	</div>

	<!-- Star histogram -->
	<Card.Root>
		<Card.Header>
			<Card.Title>Star Count Distribution</Card.Title>
		</Card.Header>
		<Card.Content>
			<BarChart data={starData} color="#6366f1" height={240} />
		</Card.Content>
	</Card.Root>

	<!-- Repo table -->
	<Card.Root>
		<Card.Content class="pt-6">
			<RepoTable repos={repos} />
		</Card.Content>
	</Card.Root>
</div>
