const { spawnSync } = require('node:child_process');

const command = process.platform === 'win32' ? 'powershell' : 'bash';
const args = process.platform === 'win32'
  ? ['-ExecutionPolicy', 'Bypass', '-File', 'scripts/validate_mvp.ps1']
  : ['scripts/validate_mvp.sh'];

const result = spawnSync(command, args, { stdio: 'inherit' });

if (result.error) {
  throw result.error;
}

process.exit(result.status ?? 1);
