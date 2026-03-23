import { prerender } from '$app/server';
import { db } from '$lib/server/db';
import { repositories, repoClassifications, orgClassifications, orgsScraped } from '$lib/server/schema';
import { eq, sql } from 'drizzle-orm';

// Shared helper: check if a DB text column has real content
function hasFeature(val: string | null): boolean {
	if (!val) return false;
	const trimmed = val.trim();
	return trimmed !== '' && trimmed !== '0' && trimmed !== 'nan' && trimmed !== 'None';
}

// ── Summary counts ──────────────────────────────────────────────────────────

export const getSummary = prerender(async () => {
	const row = db
		.select({
			total: sql<number>`count(*)`,
			totalStars: sql<number>`coalesce(sum(${repositories.stargazers_count}), 0)`,
			totalForks: sql<number>`coalesce(sum(${repositories.forks_count}), 0)`,
			uniqueLangs: sql<number>`count(distinct ${repositories.language})`,
		})
		.from(repositories)
		.innerJoin(repoClassifications, eq(repositories.full_name, repoClassifications.full_name))
		.where(eq(repoClassifications.label, 'uvm_vermont'))
		.get()!;

	return { acronym: 'UVM', ...row };
});

// ── Language distribution ───────────────────────────────────────────────────

export const getLangCounts = prerender(async () => {
	const rows = db
		.select({
			language: sql<string>`case when ${repositories.language} = 'Jupyter Notebook' then 'Jupyter' else ${repositories.language} end`,
			count: sql<number>`count(*)`,
		})
		.from(repositories)
		.innerJoin(repoClassifications, eq(repositories.full_name, repoClassifications.full_name))
		.where(eq(repoClassifications.label, 'uvm_vermont'))
		.groupBy(sql`1`)
		.having(sql`${repositories.language} is not null and trim(${repositories.language}) != ''`)
		.orderBy(sql`count(*) desc`)
		.all();

	const total = rows.reduce((s, r) => s + r.count, 0);
	const threshold = 0.03 * total;
	const counts: Record<string, number> = {};
	let other = 0;
	for (const r of rows) {
		if (r.count >= threshold) counts[r.language] = r.count;
		else other += r.count;
	}
	if (other > 0) counts['Other'] = other;
	return counts;
});

// ── License distribution ────────────────────────────────────────────────────

export const getLicenseCounts = prerender(async () => {
	const rows = db
		.select({
			license: repositories.license,
			count: sql<number>`count(*)`,
		})
		.from(repositories)
		.innerJoin(repoClassifications, eq(repositories.full_name, repoClassifications.full_name))
		.where(eq(repoClassifications.label, 'uvm_vermont'))
		.groupBy(repositories.license)
		.orderBy(sql`count(*) desc`)
		.all();

	const total = rows.reduce((s, r) => s + r.count, 0);
	const threshold = 0.03 * total;
	const counts: Record<string, number> = {};
	let other = 0;
	let noLicense = 0;

	for (const r of rows) {
		const lic = r.license?.trim();
		if (!lic || lic === 'nan' || lic === 'None') {
			noLicense += r.count;
		} else if (r.count >= threshold) {
			counts[lic] = r.count;
		} else {
			other += r.count;
		}
	}
	if (other > 0) counts['Other'] = other;
	if (noLicense > 0) counts['None'] = noLicense;
	return counts;
});

// ── Feature adoption ────────────────────────────────────────────────────────

export const getFeatureStats = prerender(async () => {
	// Use SQL to compute adoption % for each feature column
	const row = db
		.select({
			total: sql<number>`count(*)`,
			readme: sql<number>`sum(case when ${repositories.readme} is not null and trim(${repositories.readme}) != '' and trim(${repositories.readme}) != '0' and trim(${repositories.readme}) != 'nan' and trim(${repositories.readme}) != 'None' then 1 else 0 end)`,
			license: sql<number>`sum(case when ${repositories.license} is not null and trim(${repositories.license}) != '' and trim(${repositories.license}) != '0' and trim(${repositories.license}) != 'nan' and trim(${repositories.license}) != 'None' then 1 else 0 end)`,
			code_of_conduct: sql<number>`sum(case when ${repositories.code_of_conduct_file} is not null and trim(${repositories.code_of_conduct_file}) != '' and trim(${repositories.code_of_conduct_file}) != '0' and trim(${repositories.code_of_conduct_file}) != 'nan' and trim(${repositories.code_of_conduct_file}) != 'None' then 1 else 0 end)`,
			contributing: sql<number>`sum(case when ${repositories.contributing} is not null and trim(${repositories.contributing}) != '' and trim(${repositories.contributing}) != '0' and trim(${repositories.contributing}) != 'nan' and trim(${repositories.contributing}) != 'None' then 1 else 0 end)`,
			security_policy: sql<number>`sum(case when ${repositories.security_policy} is not null and trim(${repositories.security_policy}) != '' and trim(${repositories.security_policy}) != '0' and trim(${repositories.security_policy}) != 'nan' and trim(${repositories.security_policy}) != 'None' then 1 else 0 end)`,
			issue_templates: sql<number>`sum(case when ${repositories.issue_templates} is not null and trim(${repositories.issue_templates}) != '' and trim(${repositories.issue_templates}) != '0' and trim(${repositories.issue_templates}) != 'nan' and trim(${repositories.issue_templates}) != 'None' then 1 else 0 end)`,
			pr_template: sql<number>`sum(case when ${repositories.pull_request_template} is not null and trim(${repositories.pull_request_template}) != '' and trim(${repositories.pull_request_template}) != '0' and trim(${repositories.pull_request_template}) != 'nan' and trim(${repositories.pull_request_template}) != 'None' then 1 else 0 end)`,
		})
		.from(repositories)
		.innerJoin(repoClassifications, eq(repositories.full_name, repoClassifications.full_name))
		.where(eq(repoClassifications.label, 'uvm_vermont'))
		.get()!;

	const pct = (n: number) => row.total > 0 ? Math.round((n / row.total) * 1000) / 10 : 0;

	return [
		{ label: 'README', pct: pct(row.readme) },
		{ label: 'License', pct: pct(row.license) },
		{ label: 'Code of Conduct', pct: pct(row.code_of_conduct) },
		{ label: 'Contributing Guide', pct: pct(row.contributing) },
		{ label: 'Security Policy', pct: pct(row.security_policy) },
		{ label: 'Issue Templates', pct: pct(row.issue_templates) },
		{ label: 'PR Template', pct: pct(row.pr_template) },
	];
});

// ── Star distribution ───────────────────────────────────────────────────────

export const getStarBuckets = prerender(async () => {
	const rows = db
		.select({
			bucket: sql<string>`case
				when ${repositories.stargazers_count} = 0 then '0'
				when ${repositories.stargazers_count} between 1 and 4 then '1-4'
				when ${repositories.stargazers_count} between 5 and 9 then '5-9'
				when ${repositories.stargazers_count} between 10 and 49 then '10-49'
				when ${repositories.stargazers_count} between 50 and 99 then '50-99'
				when ${repositories.stargazers_count} between 100 and 499 then '100-499'
				else '500+'
			end`,
			count: sql<number>`count(*)`,
		})
		.from(repositories)
		.innerJoin(repoClassifications, eq(repositories.full_name, repoClassifications.full_name))
		.where(eq(repoClassifications.label, 'uvm_vermont'))
		.groupBy(sql`1`)
		.all();

	// Ensure correct order
	const order = ['0', '1-4', '5-9', '10-49', '50-99', '100-499', '500-999', '1000+'];
	const map = new Map(rows.map((r) => [r.bucket, r.count]));
	const buckets: Record<string, number> = {};
	for (const label of order) buckets[label] = map.get(label) ?? 0;
	return buckets;
});

// ── Top repos table ─────────────────────────────────────────────────────────

export const getTopRepos = prerender(async () => {
	const rows = db
		.select({
			full_name: repositories.full_name,
			html_url: repositories.html_url,
			description: repositories.description,
			language: repositories.language,
			license: repositories.license,
			stargazers_count: repositories.stargazers_count,
			forks_count: repositories.forks_count,
			open_issues_count: repositories.open_issues_count,
			pushed_at: repositories.pushed_at,
			readme: repositories.readme,
			code_of_conduct_file: repositories.code_of_conduct_file,
			contributing: repositories.contributing,
			security_policy: repositories.security_policy,
			issue_templates: repositories.issue_templates,
			pull_request_template: repositories.pull_request_template,
		})
		.from(repositories)
		.innerJoin(repoClassifications, eq(repositories.full_name, repoClassifications.full_name))
		.where(eq(repoClassifications.label, 'uvm_vermont'))
		.orderBy(sql`${repositories.stargazers_count} desc`)
		.limit(500)
		.all();

	return rows.map((r) => ({
		full_name: r.full_name,
		html_url: r.html_url ?? `https://github.com/${r.full_name}`,
		description: r.description ?? '',
		language: r.language ?? '',
		license: r.license ?? '',
		stargazers_count: r.stargazers_count ?? 0,
		forks_count: r.forks_count ?? 0,
		open_issues_count: r.open_issues_count ?? 0,
		pushed_at: r.pushed_at ?? '',
		has_readme: hasFeature(r.readme),
		has_license: hasFeature(r.license),
		has_code_of_conduct_file: hasFeature(r.code_of_conduct_file),
		has_contributing: hasFeature(r.contributing),
		has_security_policy: hasFeature(r.security_policy),
		has_issue_templates: hasFeature(r.issue_templates),
		has_pull_request_template: hasFeature(r.pull_request_template),
	}));
});

// ── Pipeline stats (for sankey page) ────────────────────────────────────────

function categorizeMethod(method: string | null): string {
	if (!method) return 'Other';
	if (method === 'org_owner') return 'Org Ownership';
	if (method.startsWith('user_owner')) return 'User Ownership';
	if (method === 'repo_metadata') return 'Repo Metadata';
	if (method.startsWith('readme_contains')) return 'README Signals';
	if (
		method.startsWith('langdetect') ||
		method.startsWith('spanish') ||
		method === 'non_latin_characters_in_readme'
	)
		return 'Language Detection';
	if (method === 'manual review of GitHub repo' || method === 'manual_inspection_batch')
		return 'Manual Review';
	return 'Other Heuristics';
}

function prettifyLabel(label: string): string {
	switch (label) {
		case 'uvm_vermont':
			return 'UVM Vermont';
		case 'not_uvm':
			return 'Not UVM';
		case 'uvm_mexico':
			return 'UVM Mexico';
		case 'uvm_verification':
			return 'UVM Verification';
		default:
			return label;
	}
}

function prettifySource(source: string | null): string {
	if (!source) return 'Unknown';
	if (source === 'repo_search') return 'Repo Search';
	if (source === 'org_scrape') return 'Org Scraping';
	if (source === 'user_scrape') return 'User Scraping';
	if (source.includes('+')) return 'Multiple Sources';
	return source;
}

export const getSankeyData = prerender(async () => {
	// Get raw rows with source, method, label, count
	const rows = db
		.select({
			source: repoClassifications.source,
			method: repoClassifications.method,
			label: repoClassifications.label,
			count: sql<number>`count(*)`,
		})
		.from(repoClassifications)
		.groupBy(repoClassifications.source, repoClassifications.method, repoClassifications.label)
		.all();

	// Build source → method_category flows
	const sourceToMethod = new Map<string, number>();
	// Build method_category → label flows
	const methodToLabel = new Map<string, number>();
	// Track unique node names
	const sourceNodes = new Set<string>();
	const methodNodes = new Set<string>();
	const labelNodes = new Set<string>();

	for (const r of rows) {
		const src = prettifySource(r.source);
		const cat = categorizeMethod(r.method);
		const lbl = prettifyLabel(r.label);

		sourceNodes.add(src);
		methodNodes.add(cat);
		labelNodes.add(lbl);

		const smKey = `${src}→${cat}`;
		sourceToMethod.set(smKey, (sourceToMethod.get(smKey) ?? 0) + r.count);

		const mlKey = `${cat}→${lbl}`;
		methodToLabel.set(mlKey, (methodToLabel.get(mlKey) ?? 0) + r.count);
	}

	// Assemble nodes (ordered: sources, methods, labels)
	const nodes = [
		...[...sourceNodes].map((name) => ({ name })),
		...[...methodNodes].map((name) => ({ name })),
		...[...labelNodes].map((name) => ({ name })),
	];
	const nodeIndex = new Map(nodes.map((n, i) => [n.name, i]));

	// Assemble links
	const links: { source: number; target: number; value: number }[] = [];

	for (const [key, value] of sourceToMethod) {
		const [src, tgt] = key.split('→');
		links.push({ source: nodeIndex.get(src)!, target: nodeIndex.get(tgt)!, value });
	}
	for (const [key, value] of methodToLabel) {
		const [src, tgt] = key.split('→');
		links.push({ source: nodeIndex.get(src)!, target: nodeIndex.get(tgt)!, value });
	}

	const total = rows.reduce((s, r) => s + r.count, 0);

	return { nodes, links, total };
});

// ── Pipeline steps (for ASCII view) ──────────────────────────────────────────

// Maps each raw method to which pipeline step it belongs
function pipelineStep(method: string | null): string {
	if (!method) return 'other';
	if (method === 'org_owner') return 'org';
	if (method.startsWith('user_owner')) return 'user';
	if (method === 'repo_metadata') return 'metadata';
	if (method.startsWith('readme_contains')) return 'readme';
	if (method === 'owner_has_other_uvm_vermont_repos' || method === 'owner_is_known_uvm_user')
		return 'owner_propagation';
	if (method === 'uvm_university_signal_in_text' || method === 'uvm_student_portal' ||
		method === 'former_uvm_faculty_course')
		return 'readme';
	if (
		method.startsWith('langdetect') ||
		method.startsWith('spanish') ||
		method === 'non_latin_characters_in_readme'
	)
		return 'language';
	if (
		method === 'nvidia_gpu_cuda_keywords' || method === 'verilog_hdl_keywords' ||
		method === 'vm_keywords_in_readme' || method === 'repo_named_uvm_generic' ||
		method === 'readme_contains_verification' || method === 'underwater_vehicle_keywords' ||
		method === 'vessel_monitoring_system_org' || method === 'uv_mapping_3d_graphics' ||
		method === 'uveal_melanoma_cancer_keywords' ||
		method.startsWith('owner_location_not_vermont') ||
		method.startsWith('owner_company_not_vermont')
	)
		return 'disambiguation';
	if (method === 'manual review of GitHub repo' || method === 'manual_inspection_batch')
		return 'manual';
	return 'manual'; // remaining one-off manual labels
}

export const getPipelineSteps = prerender(async () => {
	const rows = db
		.select({
			method: repoClassifications.method,
			label: repoClassifications.label,
			count: sql<number>`count(*)`,
		})
		.from(repoClassifications)
		.groupBy(repoClassifications.method, repoClassifications.label)
		.all();

	const total = rows.reduce((s, r) => s + r.count, 0);

	// Define the pipeline steps in chronological order
	const stepDefs = [
		{ id: 'org', title: 'Classify Organizations', desc: 'Review 124 GitHub orgs by name, description, location' },
		{ id: 'user', title: 'Classify Users', desc: 'Auto-classify 900 users by profile; manual review for uncertain' },
		{ id: 'metadata', title: 'Repo Metadata Propagation', desc: 'Propagate owner labels to their repos via GraphQL metadata' },
		{ id: 'readme', title: 'README & Text Signals', desc: 'Search for uvm.edu, "University of Vermont", other signals' },
		{ id: 'language', title: 'Language Detection', desc: 'Detect Spanish, non-English text to identify Mexico/foreign repos' },
		{ id: 'disambiguation', title: 'Disambiguation Heuristics', desc: 'Filter out verification, CUDA, Verilog, UV mapping, etc.' },
		{ id: 'owner_propagation', title: 'Owner Cross-referencing', desc: 'Label repos whose owners have other confirmed UVM repos' },
		{ id: 'manual', title: 'Manual Review', desc: 'Human review of uncertain cases via interactive labeling tools' },
	];

	// Aggregate counts per step and label
	const stepCounts = new Map<string, { classified: number; vermont: number; not: number; mexico: number; verification: number }>();
	for (const def of stepDefs) {
		stepCounts.set(def.id, { classified: 0, vermont: 0, not: 0, mexico: 0, verification: 0 });
	}

	for (const r of rows) {
		const step = pipelineStep(r.method);
		const entry = stepCounts.get(step);
		if (!entry) continue;
		entry.classified += r.count;
		if (r.label === 'uvm_vermont') entry.vermont += r.count;
		else if (r.label === 'not_uvm') entry.not += r.count;
		else if (r.label === 'uvm_mexico') entry.mexico += r.count;
		else if (r.label === 'uvm_verification') entry.verification += r.count;
	}

	const steps = stepDefs.map((def) => {
		const c = stepCounts.get(def.id)!;
		return { ...def, ...c };
	});

	// Final totals
	const finalVermont = steps.reduce((s, st) => s + st.vermont, 0);
	const finalNot = steps.reduce((s, st) => s + st.not, 0);
	const finalMexico = steps.reduce((s, st) => s + st.mexico, 0);
	const finalVerification = steps.reduce((s, st) => s + st.verification, 0);

	return { total, steps, final: { vermont: finalVermont, not: finalNot, mexico: finalMexico, verification: finalVerification } };
});

// ── Repos per pipeline step (for detail table) ──────────────────────────────

export const getPipelineRepos = prerender(async () => {
	const rows = db
		.select({
			full_name: repoClassifications.full_name,
			method: repoClassifications.method,
			label: repoClassifications.label,
			stargazers_count: repositories.stargazers_count,
			description: repositories.description,
			language: repositories.language,
		})
		.from(repoClassifications)
		.innerJoin(repositories, eq(repoClassifications.full_name, repositories.full_name))
		.orderBy(sql`${repositories.stargazers_count} desc`)
		.all();

	// Group by pipeline step
	const grouped: Record<string, { full_name: string; label: string; stars: number; description: string; language: string }[]> = {};
	for (const r of rows) {
		const step = pipelineStep(r.method);
		if (!grouped[step]) grouped[step] = [];
		grouped[step].push({
			full_name: r.full_name,
			label: r.label,
			stars: r.stargazers_count ?? 0,
			description: r.description ?? '',
			language: r.language ?? '',
		});
	}
	return grouped;
});

// ── Organizations page ──────────────────────────────────────────────────────

export const getOrgs = prerender(async () => {
	// Load org profiles from JSON (name, description, email, location, blog)
	const { readFileSync } = await import('fs');
	const { resolve } = await import('path');
	const profilePath = resolve('..', 'Data', 'db', 'org_profiles.json');
	const profiles: Record<string, { login: string; name: string; description: string; email: string; location: string; blog: string }> =
		JSON.parse(readFileSync(profilePath, 'utf-8'));

	// Get UVM Vermont orgs with avatar URLs
	const orgs = db
		.select({
			login: orgClassifications.login,
			label: orgClassifications.label,
			reason: orgClassifications.reason,
			avatar_url: orgsScraped.avatar_url,
		})
		.from(orgClassifications)
		.leftJoin(orgsScraped, eq(orgClassifications.login, orgsScraped.login))
		.where(eq(orgClassifications.label, 'uvm_vermont'))
		.all();

	// Count repos per org
	const repoCounts = db
		.select({
			owner: repositories.owner,
			count: sql<number>`count(*)`,
		})
		.from(repositories)
		.groupBy(repositories.owner)
		.all();

	const repoCountMap = new Map(repoCounts.map((r) => [r.owner, r.count]));

	return orgs
		.map((org) => {
			const profile = profiles[org.login];
			return {
				login: org.login,
				name: profile?.name ?? org.login,
				description: profile?.description ?? '',
				email: profile?.email ?? '',
				location: profile?.location ?? '',
				blog: profile?.blog ?? '',
				avatar_url: org.avatar_url ?? '',
				reason: org.reason ?? '',
				repo_count: repoCountMap.get(org.login) ?? 0,
			};
		})
		.filter((org) => org.repo_count > 0)
		.sort((a, b) => b.repo_count - a.repo_count);
});

// ── Time dynamics ───────────────────────────────────────────────────────────

export const getTimeSeries = prerender(async () => {
	// New repos created per year
	const created = db
		.select({
			year: sql<string>`substr(${repositories.created_at}, 1, 4)`,
			count: sql<number>`count(*)`,
		})
		.from(repositories)
		.innerJoin(repoClassifications, eq(repositories.full_name, repoClassifications.full_name))
		.where(eq(repoClassifications.label, 'uvm_vermont'))
		.groupBy(sql`1`)
		.orderBy(sql`1`)
		.all()
		.filter((r) => r.year != null);

	// Build cumulative
	let cumulative = 0;
	const byYear = created.map((r) => {
		cumulative += r.count;
		return { year: r.year, created: r.count, cumulative };
	});

	// Last push activity per year
	const pushed = db
		.select({
			year: sql<string>`substr(${repositories.pushed_at}, 1, 4)`,
			count: sql<number>`count(*)`,
		})
		.from(repositories)
		.innerJoin(repoClassifications, eq(repositories.full_name, repoClassifications.full_name))
		.where(eq(repoClassifications.label, 'uvm_vermont'))
		.groupBy(sql`1`)
		.orderBy(sql`1`)
		.all()
		.filter((r) => r.year != null);

	return { byYear, activeByYear: pushed };
});

// ── Impact: external repos citing UVM ───────────────────────────────────────

export const getImpactRepos = prerender(async () => {
	// Get owners who have at least one uvm_vermont repo (to exclude them)
	const vermontOwners = new Set(
		db
			.select({ owner: repositories.owner })
			.from(repositories)
			.innerJoin(repoClassifications, eq(repositories.full_name, repoClassifications.full_name))
			.where(eq(repoClassifications.label, 'uvm_vermont'))
			.all()
			.map((r) => r.owner)
	);

	// Find not_uvm repos whose README mentions UVM
	const rows = db
		.select({
			full_name: repositories.full_name,
			description: repositories.description,
			language: repositories.language,
			stargazers_count: repositories.stargazers_count,
			readme: repositories.readme,
		})
		.from(repositories)
		.innerJoin(repoClassifications, eq(repositories.full_name, repoClassifications.full_name))
		.where(
			sql`${repoClassifications.label} = 'not_uvm'
				AND ${repositories.readme} IS NOT NULL
				AND (lower(${repositories.readme}) LIKE '%university of vermont%'
					OR lower(${repositories.readme}) LIKE '%uvm.edu%')`
		)
		.orderBy(sql`${repositories.stargazers_count} desc`)
		.all();

	return rows
		.filter((r) => !vermontOwners.has(r.full_name.split('/')[0]))
		.map((r) => {
			// Extract ~300 char context around the UVM mention
			const readme = r.readme ?? '';
			const lower = readme.toLowerCase();
			let pos = lower.indexOf('university of vermont');
			if (pos === -1) pos = lower.indexOf('uvm.edu');
			const start = Math.max(0, pos - 100);
			const snippet = readme.substring(start, start + 300).replace(/\n/g, ' ').trim();
			const context = (start > 0 ? '...' : '') + snippet + (start + 300 < readme.length ? '...' : '');

			return {
				full_name: r.full_name,
				stars: r.stargazers_count ?? 0,
				description: r.description ?? '',
				language: r.language ?? '',
				context,
			};
		});
});
