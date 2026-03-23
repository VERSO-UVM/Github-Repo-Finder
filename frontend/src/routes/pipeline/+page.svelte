<script lang="ts">
	import { getSankeyData, getPipelineSteps, getPipelineRepos } from "../data.remote";
	import * as Card from "$lib/components/ui/card/index.js";
	import * as Table from "$lib/components/ui/table/index.js";
	import * as Tabs from "$lib/components/ui/tabs/index.js";
	import { Badge } from "$lib/components/ui/badge/index.js";
	import { Button } from "$lib/components/ui/button/index.js";
	import SankeyChart from "$lib/components/SankeyChart.svelte";
	import PipelineAscii from "$lib/components/PipelineAscii.svelte";

	const sankeyData = await getSankeyData();
	const pipelineSteps = await getPipelineSteps();
	const pipelineRepos = await getPipelineRepos();

	let selectedStep = $state<string | null>(null);

	const PAGE_SIZE = 25;
	let page = $state(0);

	// Reset page when step changes
	$effect(() => {
		selectedStep;
		page = 0;
	});

	let currentRepos = $derived.by(() => {
		if (selectedStep === null) {
			// Show all repos combined, sorted by stars
			return Object.values(pipelineRepos).flat().sort((a, b) => b.stars - a.stars);
		}
		return pipelineRepos[selectedStep] ?? [];
	});

	let paged = $derived(currentRepos.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE));
	let totalPages = $derived(Math.ceil(currentRepos.length / PAGE_SIZE));

	let tableTitle = $derived.by(() => {
		if (selectedStep === null) return 'All Repos';
		const step = pipelineSteps.steps.find((s) => s.id === selectedStep);
		return step ? step.title : selectedStep;
	});

	function labelStyle(label: string): string {
		if (label === 'uvm_vermont') return 'background-color: #154734; color: #FFD100;';
		return '';
	}

	function labelColor(label: string): "default" | "secondary" | "destructive" | "outline" {
		if (label === 'uvm_vermont') return 'default';
		if (label === 'not_uvm') return 'destructive';
		return 'secondary';
	}
</script>

<div class="p-6 w-full space-y-6 overflow-hidden">
	<div>
		<h1 class="text-3xl font-bold">Classification Pipeline</h1>
		<p class="text-muted-foreground">
			How {sankeyData.total.toLocaleString()} repositories were classified
		</p>
	</div>

	<Tabs.Root value="overview">
		<Tabs.List>
			<Tabs.Trigger value="overview">Overview</Tabs.Trigger>
			<Tabs.Trigger value="sankey">Sankey Diagram</Tabs.Trigger>
		</Tabs.List>

		<Tabs.Content value="overview" class="pt-4">
			<div class="flex gap-6 items-start">
				<!-- Left: Pipeline steps -->
				<div class="w-72 shrink-0">
					<PipelineAscii data={pipelineSteps} bind:selectedStep />
				</div>

				<!-- Right: Repo table for selected step -->
				<div class="flex-1 min-w-0">
					<Card.Root>
						<Card.Header class="pb-3">
							<Card.Title class="text-base">{tableTitle}</Card.Title>
							<p class="text-sm text-muted-foreground">{currentRepos.length.toLocaleString()} repos</p>
						</Card.Header>
						<Card.Content>
							<div class="overflow-x-auto rounded-md border">
								<Table.Root>
									<Table.Header>
										<Table.Row>
											<Table.Head>Repository</Table.Head>
											<Table.Head>Label</Table.Head>
											<Table.Head>Language</Table.Head>
											<Table.Head class="text-right">Stars</Table.Head>
										</Table.Row>
									</Table.Header>
									<Table.Body>
										{#each paged as repo (repo.full_name)}
											<Table.Row>
												<Table.Cell class="font-medium">
													<a
														href="https://github.com/{repo.full_name}"
														target="_blank"
														rel="noopener"
														class="text-blue-600 hover:underline"
													>
														{repo.full_name}
													</a>
													{#if repo.description}
														<div class="text-xs text-muted-foreground truncate max-w-md">{repo.description}</div>
													{/if}
												</Table.Cell>
												<Table.Cell>
													<Badge variant={labelColor(repo.label)} class="text-[0.65rem] px-1.5 py-0" style={labelStyle(repo.label)}>
														{repo.label.replace('_', ' ')}
													</Badge>
												</Table.Cell>
												<Table.Cell class="text-muted-foreground text-sm">{repo.language}</Table.Cell>
												<Table.Cell class="text-right tabular-nums">{repo.stars.toLocaleString()}</Table.Cell>
											</Table.Row>
										{/each}
									</Table.Body>
								</Table.Root>
							</div>

							{#if totalPages > 1}
								<div class="flex items-center gap-2 mt-3 text-sm text-muted-foreground">
									<Button variant="outline" size="sm" disabled={page === 0} onclick={() => page -= 1}>
										Prev
									</Button>
									<span>Page {page + 1} / {totalPages}</span>
									<Button variant="outline" size="sm" disabled={page >= totalPages - 1} onclick={() => page += 1}>
										Next
									</Button>
								</div>
							{/if}
						</Card.Content>
					</Card.Root>
				</div>
			</div>
		</Tabs.Content>

		<Tabs.Content value="sankey" class="pt-4">
			<Card.Root>
				<Card.Header>
					<Card.Title>Source → Method → Label</Card.Title>
				</Card.Header>
				<Card.Content>
					<SankeyChart nodes={sankeyData.nodes} links={sankeyData.links} />
				</Card.Content>
			</Card.Root>

			<Card.Root class="mt-4">
				<Card.Header>
					<Card.Title>Legend</Card.Title>
				</Card.Header>
				<Card.Content>
					<div class="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
						<div>
							<h3 class="font-semibold mb-2 flex items-center gap-2">
								<span class="inline-block w-3 h-3 rounded-sm bg-sky-500"></span>
								Source
							</h3>
							<p class="text-muted-foreground">
								Where repos were discovered: GitHub search, org scraping, or user scraping.
							</p>
						</div>
						<div>
							<h3 class="font-semibold mb-2 flex items-center gap-2">
								<span class="inline-block w-3 h-3 rounded-sm bg-amber-500"></span>
								Method
							</h3>
							<p class="text-muted-foreground">
								How they were classified: org ownership, user ownership, README signals, language detection, manual review, etc.
							</p>
						</div>
						<div>
							<h3 class="font-semibold mb-2 flex items-center gap-2">
								<span class="inline-block w-3 h-3 rounded-sm bg-green-500"></span>
								Label
							</h3>
							<p class="text-muted-foreground">
								Final classification: UVM Vermont, Not UVM, UVM Mexico, or UVM Verification.
							</p>
						</div>
					</div>
				</Card.Content>
			</Card.Root>
		</Tabs.Content>
	</Tabs.Root>
</div>
