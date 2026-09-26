"""Validate the resolved standalone production configuration without printing secrets."""
import json
import re
import subprocess
import sys


def check(condition, message):
    if not condition:
        raise SystemExit('FAIL: ' + message)


def main():
    result = subprocess.run(
        ['docker', 'compose', '-f', 'compose.prod.yaml', 'config', '--format', 'json'],
        capture_output=True, text=True, check=False,
    )
    check(result.returncode == 0, 'Compose configuration failed. Check required environment variables.')
    config = json.loads(result.stdout)
    services = config['services']
    check(config['name'] == 'civicpulse-prod', 'Use the isolated civicpulse-prod project name.')
    expected = {'frontend': {'edge'}, 'backend': {'edge', 'internal'},
                'database': {'internal'}, 'cache': {'internal'}}
    for name, networks in expected.items():
        service = services[name]
        check('build' not in service, name + ' must use a prebuilt image.')
        check(set(service['networks']) == networks, name + ' has unexpected network membership.')
        check(bool(service.get('healthcheck')), name + ' needs a healthcheck.')
        check(service.get('restart') == 'unless-stopped', name + ' needs a restart policy.')
        limits = service.get('deploy', {}).get('resources', {}).get('limits', {})
        check(bool(limits.get('cpus')) and bool(limits.get('memory')), name + ' needs resource limits.')
        check(all(v.get('type') != 'bind' for v in service.get('volumes', [])), name + ' must not bind host source.')
    for name in ['backend', 'database', 'cache']:
        check(not services[name].get('ports'), name + ' must not publish host ports.')
    for name in ['backend', 'frontend']:
        check(re.search(r':sha-[0-9a-f]{40}$', services[name]['image']), name + ' needs a full commit SHA tag.')
        check(services[name].get('read_only') is True, name + ' filesystem must be read-only.')
    for name in ['database', 'cache']:
        check(re.search(r'@sha256:[0-9a-f]{64}$', services[name]['image']), name + ' must use a registry digest.')
    check(config['networks']['internal'].get('internal') is True, 'Data network must be internal.')
    check('--reload' not in services['backend'].get('command', []), 'Production must not use reload.')
    check({'pgdata', 'redisdata', 'ollama_models'} <= set(config['volumes']), 'Missing persistent volumes.')
    check(all('build' not in s for s in services.values()), 'No production service may build images.')
    print('PASS: prebuilt SHA images, pinned data images, isolated networks, healthchecks, limits, persistence and no source mounts')


if __name__ == '__main__':
    try:
        main()
    except (KeyError, ValueError, FileNotFoundError) as error:
        sys.exit('FAIL: invalid configuration or Docker unavailable (' + type(error).__name__ + ')')
