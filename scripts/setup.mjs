#!/usr/bin/env node
// One-time setup:  npm run setup
// Checks the tools the pipeline needs, installs the HyperFrames skills for Claude Code, and lists the
// optional music and sound downloads. Safe to run again at any time.
// Reels pin an exact HyperFrames version on purpose: never run `hyperframes upgrade` here.
import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { findPython } from './py.mjs';
import { HYPERFRAMES, OPTIONAL_AUDIO, bundledSfxDir } from './paths.mjs';

const windows = process.platform === 'win32';
// npm-installed commands are .cmd files on Windows and only start through a shell.
const run = (command, args, options = {}) => spawnSync(command, args, { shell: windows, encoding: 'utf8', ...options });
const works = (command, args) => run(command, args, { stdio: 'ignore' }).status === 0;

const INSTALL = {
	node: { win32: 'winget install OpenJS.NodeJS.LTS', darwin: 'brew install node', linux: 'https://nodejs.org (LTS) or your package manager' },
	python: { win32: 'winget install Python.Python.3.12', darwin: 'brew install python', linux: 'sudo apt install python3  (or: sudo dnf install python3)' },
	ffmpeg: { win32: 'winget install Gyan.FFmpeg', darwin: 'brew install ffmpeg', linux: 'sudo apt install ffmpeg  (or: sudo dnf install ffmpeg)' },
	claude: {
		win32: 'winget install Anthropic.ClaudeCode  (more options: https://code.claude.com/docs/en/setup)',
		darwin: 'curl -fsSL https://claude.ai/install.sh | bash  (more options: https://code.claude.com/docs/en/setup)',
		linux: 'curl -fsSL https://claude.ai/install.sh | bash  (more options: https://code.claude.com/docs/en/setup)',
	},
};
const how = (tool) => INSTALL[tool][process.platform] ?? INSTALL[tool].linux;

const problems = [];
const check = (label, ok, tool, detail = '') => {
	console.log(`  ${ok ? '✓' : '✗'} ${label}${detail ? `  ${detail}` : ''}`);
	if (!ok) problems.push(`${label}: ${how(tool)}`);
};

console.log('\nChecking your computer\n');
const nodeMajor = Number(process.versions.node.split('.')[0]);
check('Node.js 22 or newer', nodeMajor >= 22, 'node', `(found ${process.versions.node})`);
const python = findPython();
check('Python 3.10 or newer', Boolean(python), 'python', python ? `(${python.join(' ')})` : '');
check('FFmpeg', works('ffmpeg', ['-version']) && works('ffprobe', ['-version']), 'ffmpeg');
check('Claude Code', works('claude', ['--version']), 'claude');

if (problems.length) {
	console.log('\nInstall what is missing, close this terminal, open a new one in this folder and run `npm run setup` again:\n');
	for (const problem of problems) console.log(`  • ${problem}`);
	process.exit(1);
}

console.log('\nInstalling the HyperFrames skills for Claude Code (a minute or two)\n');
const skills = run('npx', ['--yes', HYPERFRAMES, 'skills'], { stdio: 'inherit' });
if (skills.status !== 0) {
	console.log('\nThe skills could not be installed. Check your internet connection and run `npm run setup` again.');
	process.exit(1);
}
check('HyperFrames sound effects', Boolean(bundledSfxDir()), 'claude', bundledSfxDir() ?? '');

console.log('\nInstalling the browser HyperFrames renders with (once, ~115 MB)\n');
const browser = run('npx', ['--yes', HYPERFRAMES, 'browser', 'ensure'], { stdio: 'inherit' });
if (browser.status !== 0) {
	console.log('\nThe browser could not be installed. Check your internet connection and run `npm run setup` again.');
	process.exit(1);
}

console.log('\nInstalling the speech-to-text model for subtitles (once, ~650 MB; runs on your computer)\n');
const model = run('npx', ['--yes', HYPERFRAMES, 'models', 'install', 'parakeet'], { stdio: 'inherit' });
if (model.status !== 0) {
	console.log('\nThe speech-to-text model could not be installed. Check your internet connection and free disk space, then run `npm run setup` again.');
	process.exit(1);
}


console.log('\nOptional music and sounds (the reels work without them)\n');
for (const [dir, file] of OPTIONAL_AUDIO) console.log(`  ${existsSync(join(dir, file)) ? '✓' : '·'} ${file}`);
console.log('  How to get them: _shared/music/README.md and _shared/sfx/README.md');

console.log('\nAll set. Create your first reel with:  npm run new-reel MyFirstReel\n');
