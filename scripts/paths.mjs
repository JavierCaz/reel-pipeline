// Shared locations for setup.mjs and new-reel.mjs.
import { existsSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
export const TEMPLATE = join(ROOT, '_templates', 'short-template');
export const SHORTS = join(ROOT, 'Shorts');
export const SHARED_MUSIC = join(ROOT, '_shared', 'music');
export const SHARED_SFX = join(ROOT, '_shared', 'sfx');

/** Exact HyperFrames version every reel uses (pinned in the template's package.json). */
export const HYPERFRAMES = 'hyperframes@0.8.92';

/** Optional downloads (see _shared/music/README.md and _shared/sfx/README.md); names must match presets.py. */
export const OPTIONAL_AUDIO = [
	[SHARED_MUSIC, 'velariomusic-lofi-relaxing-598427.mp3'],
	[SHARED_SFX, 'creatorshome-turn-a-page-336933.mp3'],
	[SHARED_SFX, 'soundreality-whoosh-flame-388763.mp3'],
	[SHARED_SFX, 'oxidvideos-transition-sfx-2-409073.mp3'],
	[SHARED_SFX, 'soundreality-whoosh-vortex-2-388197.mp3'],
];

/** The sound effects bundled with the HyperFrames media-use skill, once `npm run setup` installed the skills. */
export function bundledSfxDir() {
	const candidates = ['.claude', '.agents', '.codex'].map((tool) => join(homedir(), tool, 'skills', 'media-use', 'audio', 'assets', 'sfx'));
	return candidates.find((dir) => existsSync(join(dir, 'whoosh.mp3'))) ?? null;
}
