<script lang="ts">
	import * as Table from "$lib/components/ui/table/index.js";
	import { Badge } from "$lib/components/ui/badge/index.js";
	import { Button } from "$lib/components/ui/button/index.js";
	import { Input } from "$lib/components/ui/input/index.js";

	interface Repo {
		full_name: string;
		html_url: string;
		description: string;
		language: string;
		license: string;
		stargazers_count: number;
		forks_count: number;
		open_issues_count: number;
		pushed_at: string;
		has_readme: boolean;
		has_license: boolean;
		has_code_of_conduct_file: boolean;
		has_contributing: boolean;
		has_security_policy: boolean;
		has_issue_templates: boolean;
		has_pull_request_template: boolean;
	}

	let { repos }: { repos: Repo[] } = $props();

	const PAGE_SIZE = 25;

	const FEATURE_COLS: [keyof Repo, string][] = [
		["has_readme", "README"],
		["has_license", "License"],
		["has_code_of_conduct_file", "CoC"],
		["has_contributing", "Contrib"],
		["has_security_policy", "Security"],
		["has_issue_templates", "Issues"],
		["has_pull_request_template", "PR Tmpl"]
	];

	const NUM_COLS = ["stargazers_count", "forks_count", "open_issues_count"];

	let search = $state("");
	let sortCol = $state<keyof Repo>("stargazers_count");
	let sortDir = $state(-1);
	let page = $state(0);

	let filtered = $derived.by(() => {
		const q = search.toLowerCase();
		let result = repos.filter(
			(r) =>
				r.full_name.toLowerCase().includes(q) ||
				r.language.toLowerCase().includes(q) ||
				r.description.toLowerCase().includes(q)
		);

		const isNum = NUM_COLS.includes(sortCol);
		result.sort((a, b) => {
			const av = isNum ? (a[sortCol] as number) : String(a[sortCol]).toLowerCase();
			const bv = isNum ? (b[sortCol] as number) : String(b[sortCol]).toLowerCase();
			if (av < bv) return -sortDir;
			if (av > bv) return sortDir;
			return 0;
		});

		return result;
	});

	let paged = $derived(filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE));
	let totalPages = $derived(Math.ceil(filtered.length / PAGE_SIZE));

	function toggleSort(col: keyof Repo) {
		if (sortCol === col) {
			sortDir *= -1;
		} else {
			sortCol = col;
			sortDir = -1;
		}
		page = 0;
	}
</script>

<div class="space-y-3">
	<div class="flex items-center justify-between">
		<h2 class="font-semibold">Repositories (top 500 by stars)</h2>
		<Input
			placeholder="Search..."
			class="w-56"
			value={search}
			oninput={(e: Event) => {
				search = (e.target as HTMLInputElement).value;
				page = 0;
			}}
		/>
	</div>

	<div class="overflow-x-auto rounded-md border">
		<Table.Root>
			<Table.Header>
				<Table.Row>
					<Table.Head class="cursor-pointer" onclick={() => toggleSort("full_name")}>
						Repository
					</Table.Head>
					<Table.Head class="cursor-pointer" onclick={() => toggleSort("language")}>
						Language
					</Table.Head>
					<Table.Head class="cursor-pointer" onclick={() => toggleSort("license")}>
						License
					</Table.Head>
					<Table.Head
						class="cursor-pointer text-right"
						onclick={() => toggleSort("stargazers_count")}
					>
						Stars
					</Table.Head>
					<Table.Head
						class="cursor-pointer text-right"
						onclick={() => toggleSort("forks_count")}
					>
						Forks
					</Table.Head>
					<Table.Head>Features</Table.Head>
					<Table.Head class="cursor-pointer" onclick={() => toggleSort("pushed_at")}>
						Last Push
					</Table.Head>
				</Table.Row>
			</Table.Header>
			<Table.Body>
				{#each paged as repo}
					<Table.Row>
						<Table.Cell class="font-medium">
							<a
								href={repo.html_url}
								target="_blank"
								rel="noopener"
								class="text-blue-600 hover:underline"
							>
								{repo.full_name}
							</a>
						</Table.Cell>
						<Table.Cell class="text-muted-foreground">{repo.language}</Table.Cell>
						<Table.Cell class="text-muted-foreground">{repo.license}</Table.Cell>
						<Table.Cell class="text-right">
							{repo.stargazers_count.toLocaleString()}
						</Table.Cell>
						<Table.Cell class="text-right">
							{repo.forks_count.toLocaleString()}
						</Table.Cell>
						<Table.Cell class="whitespace-nowrap">
							{#each FEATURE_COLS as [col, lbl]}
								<Badge variant={repo[col] ? "default" : "outline"} class="mr-0.5 text-[0.65rem] px-1.5 py-0">
									{lbl}
								</Badge>
							{/each}
						</Table.Cell>
						<Table.Cell class="text-muted-foreground">
							{repo.pushed_at ? repo.pushed_at.slice(0, 10) : ""}
						</Table.Cell>
					</Table.Row>
				{/each}
			</Table.Body>
		</Table.Root>
	</div>

	<div class="flex items-center gap-2 text-sm text-muted-foreground">
		<Button variant="outline" size="sm" disabled={page === 0} onclick={() => (page -= 1)}>
			Prev
		</Button>
		<span>Page {page + 1} / {totalPages} ({filtered.length} repos)</span>
		<Button
			variant="outline"
			size="sm"
			disabled={page >= totalPages - 1}
			onclick={() => (page += 1)}
		>
			Next
		</Button>
	</div>
</div>
