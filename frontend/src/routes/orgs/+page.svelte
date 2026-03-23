<script lang="ts">
	import { getOrgs } from "../data.remote";
	import * as Card from "$lib/components/ui/card/index.js";
	import { Badge } from "$lib/components/ui/badge/index.js";

	const orgs = await getOrgs();
</script>

<div class="p-6 w-full space-y-6 overflow-hidden">
	<div>
		<h1 class="text-3xl font-bold">Organizations</h1>
		<p class="text-muted-foreground">
			{orgs.length} UVM-affiliated GitHub organizations
		</p>
	</div>

	<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
		{#each orgs as org (org.login)}
			<a
				href="https://github.com/{org.login}"
				target="_blank"
				rel="noopener"
				class="block"
			>
				<Card.Root class="h-full hover:shadow-md transition-shadow">
					<Card.Header class="pb-3">
						<div class="flex items-center gap-3 min-w-0">
							<img
								src={org.avatar_url}
								alt="{org.login} avatar"
								class="w-12 h-12 shrink-0 rounded-full"
							/>
							<div class="min-w-0 overflow-hidden">
								<Card.Title class="text-base truncate">{org.name}</Card.Title>
								<p class="text-sm text-muted-foreground truncate">@{org.login}</p>
							</div>
						</div>
					</Card.Header>
					<Card.Content class="pt-0 space-y-3">
						{#if org.description}
							<p class="text-sm text-muted-foreground line-clamp-2">{org.description}</p>
						{/if}

						<div class="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
							{#if org.location}
								<span>{org.location}</span>
							{/if}
							{#if org.blog}
								<a
									href={org.blog.startsWith("http") ? org.blog : `https://${org.blog}`}
									target="_blank"
									rel="noopener"
									class="truncate max-w-[180px] hover:underline text-blue-600"
									onclick={(e) => e.stopPropagation()}
								>
									{org.blog.replace(/^https?:\/\//, "")}
								</a>
							{/if}
						</div>

						<div>
							<Badge style="background-color: #154734; color: #FFD100;">
								{org.repo_count} repos
							</Badge>
						</div>
					</Card.Content>
				</Card.Root>
			</a>
		{/each}
	</div>
</div>
