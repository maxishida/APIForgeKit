const { existsSync, statSync } = require('node:fs');
const { resolve } = require('node:path');
const { spawnSync } = require('node:child_process');

const [action, ...args] = process.argv.slice(2);
const vaultFlag = args.indexOf('--vault');

if (!['sync', 'validate'].includes(action) || vaultFlag < 0 || !args[vaultFlag + 1]) {
  process.stderr.write('Usage: npm run obsidian:<sync|validate> -- --vault <existing-vault-path>\n');
  process.exit(2);
}

const vaultPath = resolve(args[vaultFlag + 1]);
if (!existsSync(vaultPath) || !statSync(vaultPath).isDirectory()) {
  process.stderr.write(`Vault directory does not exist: ${vaultPath}\n`);
  process.exit(2);
}

const root = resolve(__dirname, '..');
const gitValue = (...gitArgs) => {
  const result = spawnSync('git', gitArgs, { cwd: root, encoding: 'utf8' });
  return result.status === 0 ? result.stdout.trim() || 'unknown' : 'unknown';
};
const dockerArgs = [
  'run', '--rm',
  '-v', `${root}:/app`,
  '-v', `${vaultPath}:/vault`,
  '-w', '/app',
  '-e', `APIFORGEKIT_GIT_BRANCH=${gitValue('branch', '--show-current')}`,
  '-e', `APIFORGEKIT_GIT_COMMIT=${gitValue('rev-parse', '--short', 'HEAD')}`,
  '-e', `APIFORGEKIT_GIT_SUBJECT=${gitValue('log', '-1', '--pretty=%s')}`,
  'python:3.13-slim', 'python', 'scripts/sync_obsidian_vault.py', action, '--vault', "/vault",
];
const result = spawnSync('docker', dockerArgs, { stdio: 'inherit' });
if (result.error) throw result.error;
process.exit(result.status ?? 1);
