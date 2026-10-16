#!/usr/bin/env node
// Runs a Python script with whichever Python 3.10+ this computer has: `python3` (macOS, Linux),
// `python` or `py -3` (Windows). Reel folders call it from package.json:
//   node ../../scripts/py.mjs ../../_shared/pipeline/build.py <step> ...
import { spawnSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';

const CANDIDATES = [['python3'], ['python'], ['py', '-3']];
const VERSION_CHECK = 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)';

/** The first Python 3.10+ command found, as [command, ...prefix args], or null. */
export function findPython() {
	for (const candidate of CANDIDATES) {
		const [command, ...prefix] = candidate;
		const probe = spawnSync(command, [...prefix, '-c', VERSION_CHECK], { stdio: 'ignore' });
		if (probe.status === 0) return candidate;
	}
	return null;
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
	const python = findPython();
	if (!python) {
		console.error('Python 3.10 or newer was not found. Install it (see the guide, chapter 3), then open a new terminal.');
		process.exit(1);
	}
	const [command, ...prefix] = python;
	const run = spawnSync(command, [...prefix, ...process.argv.slice(2)], { stdio: 'inherit' });
	process.exit(run.status ?? 1);
}
