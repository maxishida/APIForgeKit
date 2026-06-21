const { resolve } = require('node:path');
const { spawnSync } = require('node:child_process');

const action = process.argv[2];
const verbose = process.argv.includes('--verbose');
if (!['dry', 'apply'].includes(action)) {
  process.stderr.write('Usage: npm run demo:clean:dry | npm run demo:clean\n');
  process.exit(2);
}

const dockerInfo = spawnSync('docker', ['info'], { stdio: 'ignore' });
if (dockerInfo.error || dockerInfo.status !== 0) {
  process.stderr.write('Docker Desktop/Engine não está pronto. Inicie o Docker e execute o comando novamente.\n');
  process.exit(1);
}

const root = resolve(__dirname, '..');
const command = ['python', 'scripts/clean_demo_artifacts.py'];
if (action === 'apply') command.push('--apply');
if (verbose) command.push('--verbose');

const result = spawnSync(
  'docker',
  ['run', '--rm', '-v', `${root}:/app`, '-w', '/app', 'python:3.13-slim', ...command],
  { stdio: 'inherit' },
);

if (result.error) throw result.error;
process.exit(result.status ?? 1);
