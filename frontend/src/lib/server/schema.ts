import { sqliteTable, text, integer, real } from 'drizzle-orm/sqlite-core';

export const repositories = sqliteTable('repositories', {
	full_name: text('full_name').primaryKey(),
	name: text('name'),
	owner: text('owner'),
	html_url: text('html_url'),
	description: text('description'),
	language: text('language'),
	license: text('license'),
	stargazers_count: integer('stargazers_count'),
	forks_count: integer('forks_count'),
	open_issues_count: integer('open_issues_count'),
	created_at: text('created_at'),
	updated_at: text('updated_at'),
	pushed_at: text('pushed_at'),
	size: integer('size'),
	archived: integer('archived'),
	fork: integer('fork'),
	readme: text('readme'),
	code_of_conduct_file: text('code_of_conduct_file'),
	contributing: text('contributing'),
	security_policy: text('security_policy'),
	issue_templates: text('issue_templates'),
	pull_request_template: text('pull_request_template'),
});

export const repoClassifications = sqliteTable('repo_classifications', {
	full_name: text('full_name').primaryKey(),
	label: text('label').notNull(),
	method: text('method'),
	labeled_by: text('labeled_by'),
	source: text('source'),
});

export const orgClassifications = sqliteTable('org_classifications', {
	login: text('login').primaryKey(),
	label: text('label').notNull(),
	reason: text('reason'),
	labeled_by: text('labeled_by'),
});

export const userClassifications = sqliteTable('user_classifications', {
	login: text('login').primaryKey(),
	label: text('label').notNull(),
	reason: text('reason'),
	labeled_by: text('labeled_by'),
});

export const orgsScraped = sqliteTable('orgs_scraped', {
	login: text('login'),
	avatar_url: text('avatar_url'),
});
