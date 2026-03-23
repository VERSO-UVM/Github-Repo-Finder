<script lang="ts">
	type Step = {
		id: string;
		title: string;
		desc: string;
		classified: number;
		vermont: number;
		not: number;
		mexico: number;
		verification: number;
	};

	type PipelineData = {
		total: number;
		steps: Step[];
		final: { vermont: number; not: number; mexico: number; verification: number };
	};

	let { data, selectedStep = $bindable(null) }: { data: PipelineData; selectedStep?: string | null } = $props();

	let remaining = $derived.by(() => {
		let r = data.total;
		return data.steps.map((step) => {
			const before = r;
			r -= step.classified;
			return { before, after: r };
		});
	});
</script>

<div class="font-mono flex flex-col items-center gap-0 w-full text-sm">
	<!-- Start -->
	<button
		class="w-full border rounded-lg px-4 py-3 text-center text-left cursor-pointer transition-colors {selectedStep === null ? 'border-primary bg-primary/5 ring-1 ring-primary/20' : 'border-border bg-card hover:bg-muted/50'}"
		onclick={() => selectedStep = null}
	>
		<div class="font-bold text-base text-foreground">{data.total.toLocaleString()} candidate repos</div>
		<div class="text-xs text-muted-foreground">scraped from GitHub (repos, orgs, users)</div>
	</button>

	{#each data.steps as step, i (step.id)}
		<!-- Connector with remaining count -->
		<div class="flex flex-col items-center">
			<div class="w-px h-3 border-l-2 border-dashed border-muted-foreground/40"></div>
			<div class="text-[0.65rem] text-muted-foreground tabular-nums">{remaining[i].before.toLocaleString()} unclassified</div>
			<div class="w-px h-3 border-l-2 border-dashed border-muted-foreground/40"></div>
		</div>

		<!-- Step box (clickable) -->
		<button
			class="w-full border rounded-lg text-left cursor-pointer transition-colors {selectedStep === step.id ? 'border-primary bg-primary/5 ring-1 ring-primary/20' : 'border-border bg-card hover:bg-muted/50'}"
			onclick={() => selectedStep = step.id}
		>
			<div class="px-3 py-1.5 border-b border-border rounded-t-lg flex items-baseline justify-between gap-2 {selectedStep === step.id ? 'bg-primary/10' : 'bg-muted/50'}">
				<span class="font-semibold text-[0.65rem] uppercase tracking-wider text-muted-foreground">Step {i + 1}</span>
				<span class="text-[0.65rem] text-muted-foreground">{step.classified.toLocaleString()} classified</span>
			</div>
			<div class="px-3 py-2">
				<div class="font-semibold text-xs">{step.title}</div>
				<div class="text-[0.65rem] text-muted-foreground mb-1">{step.desc}</div>
				<div class="flex flex-wrap gap-x-3 gap-y-0.5 text-[0.65rem]">
					{#if step.vermont > 0}
						<span style="color: #154734">+{step.vermont.toLocaleString()} vermont</span>
					{/if}
					{#if step.not > 0}
						<span class="text-red-500 dark:text-red-400">-{step.not.toLocaleString()} not uvm</span>
					{/if}
					{#if step.mexico > 0}
						<span class="text-amber-600 dark:text-amber-400">+{step.mexico.toLocaleString()} mexico</span>
					{/if}
					{#if step.verification > 0}
						<span class="text-purple-600 dark:text-purple-400">+{step.verification.toLocaleString()} verification</span>
					{/if}
				</div>
			</div>
		</button>
	{/each}

	<!-- Final connector -->
	<div class="w-px h-4 border-l-2 border-dashed border-muted-foreground/40"></div>

	<!-- Final result -->
	<div class="w-full border-2 rounded-lg px-3 py-2" style="border-color: #154734; background-color: #154734">
		<div class="font-bold text-center text-xs mb-1" style="color: #FFD100">Final Classification</div>
		<div class="space-y-0.5 text-xs" style="color: #ffffffcc">
			<div class="flex items-baseline gap-1">
				<span class="shrink-0" style="color: #FFD100">UVM Vermont</span>
				<span class="flex-1 border-b border-dotted min-w-4 translate-y-[-3px]" style="border-color: #ffffff40"></span>
				<span class="shrink-0 tabular-nums font-semibold" style="color: #FFD100">{data.final.vermont.toLocaleString()}</span>
			</div>
			<div class="flex items-baseline gap-1">
				<span class="shrink-0" style="color: #ff9999">Not UVM</span>
				<span class="flex-1 border-b border-dotted min-w-4 translate-y-[-3px]" style="border-color: #ffffff40"></span>
				<span class="shrink-0 tabular-nums font-semibold">{data.final.not.toLocaleString()}</span>
			</div>
			<div class="flex items-baseline gap-1">
				<span class="shrink-0" style="color: #ffcc66">UVM Mexico</span>
				<span class="flex-1 border-b border-dotted min-w-4 translate-y-[-3px]" style="border-color: #ffffff40"></span>
				<span class="shrink-0 tabular-nums font-semibold">{data.final.mexico.toLocaleString()}</span>
			</div>
			<div class="flex items-baseline gap-1">
				<span class="shrink-0" style="color: #cc99ff">UVM Verification</span>
				<span class="flex-1 border-b border-dotted min-w-4 translate-y-[-3px]" style="border-color: #ffffff40"></span>
				<span class="shrink-0 tabular-nums font-semibold">{data.final.verification.toLocaleString()}</span>
			</div>
		</div>
	</div>
</div>
