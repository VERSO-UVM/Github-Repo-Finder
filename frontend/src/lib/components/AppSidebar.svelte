<script lang="ts">
	import { base } from "$app/paths";
	import { page } from "$app/state";
	import * as Sidebar from "$lib/components/ui/sidebar/index.js";
	import { LayoutDashboardIcon, GitBranchIcon, Building2Icon, TrendingUpIcon, SparklesIcon, GithubIcon } from "@lucide/svelte";
	import versoLogo from "$lib/assets/verso.png";

	const navItems = [
		{ title: "Dashboard", url: "/", icon: LayoutDashboardIcon },
		{ title: "Pipeline", url: "/pipeline", icon: GitBranchIcon },
		{ title: "Organizations", url: "/orgs", icon: Building2Icon },
		{ title: "Trends", url: "/trends", icon: TrendingUpIcon },
		{ title: "Impact", url: "/impact", icon: SparklesIcon },
	];
</script>

<Sidebar.Root collapsible="icon">
	<Sidebar.Header class="p-4">
		<a href="{base}/" class="flex items-center gap-3">
			<img
				src={versoLogo}
				alt="VERSO logo"
				width="60"
				height="60"
				class="shrink-0 rounded-full"
			/>
			<div class="group-data-[collapsible=icon]:hidden flex flex-col gap-0.5 leading-none">
				<span class="font-semibold">VERSO</span>
				<span class="text-xs text-muted-foreground">UVM Repofinder</span>
			</div>
		</a>
	</Sidebar.Header>

	<Sidebar.Separator />

	<Sidebar.Content>
		<Sidebar.Group>
			<Sidebar.GroupLabel>Navigation</Sidebar.GroupLabel>
			<Sidebar.GroupContent>
				<Sidebar.Menu>
					{#each navItems as item (item.title)}
						<Sidebar.MenuItem>
							<Sidebar.MenuButton
								isActive={page.url.pathname === `${base}${item.url}` || (item.url === '/' && page.url.pathname === `${base}`)}
								tooltipContent={item.title}
							>
								{#snippet child({ props })}
									<a href="{base}{item.url}" {...props}>
										<item.icon />
										<span>{item.title}</span>
									</a>
								{/snippet}
							</Sidebar.MenuButton>
						</Sidebar.MenuItem>
					{/each}
				</Sidebar.Menu>
			</Sidebar.GroupContent>
		</Sidebar.Group>
	</Sidebar.Content>

	<Sidebar.Footer>
		<Sidebar.Menu>
			<Sidebar.MenuItem>
				<Sidebar.MenuButton>
					{#snippet child({ props })}
						<a
							href="https://github.com/jstonge1/repofinder"
							target="_blank"
							rel="noopener"
							{...props}
						>
							<GithubIcon />
							<span>Source Code</span>
						</a>
					{/snippet}
				</Sidebar.MenuButton>
			</Sidebar.MenuItem>
		</Sidebar.Menu>
	</Sidebar.Footer>

	<Sidebar.Rail />
</Sidebar.Root>
