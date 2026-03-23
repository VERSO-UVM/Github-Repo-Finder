<script lang="ts">
	import { getImpactRepos } from "../data.remote";
	import * as Card from "$lib/components/ui/card/index.js";
	import * as Table from "$lib/components/ui/table/index.js";
	import { Button } from "$lib/components/ui/button/index.js";

	const repos = await getImpactRepos();

	const PAGE_SIZE = 25;
	let page = $state(0);
	let totalPages = $derived(Math.ceil(repos.length / PAGE_SIZE));
	let paged = $derived(repos.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE));
</script>

<div class="p-6 w-full space-y-6 overflow-hidden">
	<div>
		<h1 class="text-3xl font-bold">Impact</h1>
		<p class="text-muted-foreground">
			{repos.length} external repos citing UVM work
		</p>
	</div>

	<Card.Root>
		<Card.Header>
			<Card.Title>External Repos Mentioning UVM</Card.Title>
			<p class="text-sm text-muted-foreground">
				Non-UVM repositories that reference "University of Vermont" or uvm.edu in their README
			</p>
		</Card.Header>
		<Card.Content>
			<div class="overflow-x-auto rounded-md border">
				<Table.Root>
					<Table.Header>
						<Table.Row>
							<Table.Head>Repository</Table.Head>
							<Table.Head>Language</Table.Head>
							<Table.Head class="text-right">Stars</Table.Head>
							<Table.Head class="min-w-[250px]">UVM Mention</Table.Head>
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
								<Table.Cell class="text-muted-foreground text-sm">{repo.language}</Table.Cell>
								<Table.Cell class="text-right tabular-nums">{repo.stars.toLocaleString()}</Table.Cell>
								<Table.Cell class="whitespace-normal">
									<p class="text-xs text-muted-foreground line-clamp-3 min-w-[250px] max-w-md">{repo.context}</p>
								</Table.Cell>
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
