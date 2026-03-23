import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import * as schema from './schema.js';
import { resolve } from 'path';

const DB_PATH = resolve(process.cwd(), '..', 'Data', 'db', 'repository_data_UVM_database.db');
const sqlite = new Database(DB_PATH, { readonly: true });

export const db = drizzle(sqlite, { schema });
