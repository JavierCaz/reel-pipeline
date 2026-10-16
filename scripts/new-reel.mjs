#!/usr/bin/env node
// Creates Shorts/<Name> from the template:  npm run new-reel <Name>
// Copies (never links) the bundled and optional sounds into the reel, so it works the same on
// Windows, macOS and Linux; HyperFrames only reads media inside the reel folder.
import { copyFileSync, cpSync, existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join, relative } from 'node:path';
import { SHARED_MUSIC, SHARED_SFX, SHORTS, TEMPLATE, bundledSfxDir } from './paths.mjs';

const name = process.argv[2];
if (!name || !/^[A-Za-z0-9][A-Za-z0-9_-]*$/.test(name)) {
	console.error('Usage: npm run new-reel <Name>   (letters, numbers, - and _; no spaces), e.g. npm run new-reel MyFirstReel');
	process.exit(1);
}
const reel = join(SHORTS, name);
if (existsSync(reel)) {
	console.error(`${relative(process.cwd(), reel)} already exists. Pick another name.`);
	process.exit(1);
}

cpSync(TEMPLATE, reel, { recursive: true });

const audio = (file) => /\.(mp3|wav|m4a|ogg|mp4)$/i.test(file);
const copyAudio = (from, to) => {
	mkdirSync(to, { recursive: true });
	const files = existsSync(from) ? readdirSync(from).filter(audio) : [];
	for (const file of files) copyFileSync(join(from, file), join(to, file));
	return files.length;
};

const bundled = bundledSfxDir();
const sfxCount = bundled ? copyAudio(bundled, join(reel, 'media', 'audio', 'sfx')) : 0;
const optional = copyAudio(SHARED_MUSIC, join(reel, 'media', 'audio', 'shared-music')) + copyAudio(SHARED_SFX, join(reel, 'media', 'audio', 'shared-sfx'));

const pkgPath = join(reel, 'package.json');
const pkg = JSON.parse(readFileSync(pkgPath, 'utf8'));
pkg.name = name.toLowerCase().replace(/_/g, '-');
writeFileSync(pkgPath, `${JSON.stringify(pkg, null, 2)}\n`);

console.log(`Created ${relative(process.cwd(), reel)}`);
if (bundled) console.log(`  ${sfxCount} sound effects copied from the HyperFrames skills`);
else console.log('  ! The HyperFrames sound effects were not found: run `npm run setup` first, then create the reel again.');
console.log(`  ${optional} optional music/sound files copied from _shared/ (the reel works without them)`);
console.log(`\nNext: put your clips in ${relative(process.cwd(), join(reel, 'media', 'raw'))}, open Claude Code in the reel-pipeline folder (type "claude") and paste the kickoff prompt.`);
