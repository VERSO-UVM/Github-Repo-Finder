<script lang="ts">
	import * as Card from "$lib/components/ui/card/index.js";

	let { icon, value, label }: { icon: string; value: string; label: string } = $props();
</script>

<Card.Root class="text-center">
	<Card.Content class="pt-6">
		<div class="text-3xl mb-1">{icon}</div>
		<div class="text-2xl font-bold">{value}</div>
		<p class="text-sm text-muted-foreground">{label}</p>
	</Card.Content>
</Card.Root>
