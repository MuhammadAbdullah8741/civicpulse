"""Scan built images with pinned Trivy; preserve JSON reports even when the gate fails."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

SCANNER = 'aquasec/trivy:0.74.0'


def scan(image: str, index: int, output: Path) -> bool:
    report = output / f'image-{index}-trivy.json'
    if report.exists():
        report.unlink()  # Never present a previous successful report as this run's result.
    with tempfile.TemporaryDirectory(prefix='civicpulse-scan-') as folder:
        work = Path(folder)
        print(f'Exporting {image}', flush=True)
        subprocess.run(['docker', 'save', '--output', str(work / 'image.tar'), image], check=True)
        command = [
            'docker', 'run', '--rm',
            '--mount', f'type=bind,source={work},target=/scan',
            '--mount', 'type=volume,source=civicpulse-trivy-cache,target=/root/.cache/trivy',
            SCANNER, 'image', '--input', '/scan/image.tar',
            '--scanners', 'vuln', '--ignore-unfixed',
            '--severity', 'HIGH,CRITICAL', '--exit-code', '1',
            '--timeout', '15m', '--format', 'json', '--output', '/scan/report.json',
        ]
        result = subprocess.run(command, check=False)
        produced = work / 'report.json'
        if not produced.exists():
            print(f'FAIL: {image}: scanner did not produce a report (exit {result.returncode}).', flush=True)
            return False
        report.write_bytes(produced.read_bytes())
        data = json.loads(report.read_text(encoding='utf-8'))
        findings = [v for section in data.get('Results', [])
                    for v in section.get('Vulnerabilities', [])]
        print(f'{image}: {len(findings)} fixable HIGH/CRITICAL findings', flush=True)
        for finding in findings:
            print(' | '.join(str(finding.get(key, '')) for key in (
                'VulnerabilityID', 'Severity', 'PkgName', 'InstalledVersion', 'FixedVersion'
            )), flush=True)
        print(f'Report: {report}', flush=True)
        if result.returncode != 0 or findings:
            print(f'FAIL: {image}', flush=True)
            return False
        print(f'PASS: {image}', flush=True)
        return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('images', nargs='+', help='Local built image references to scan')
    parser.add_argument('--output', type=Path,
                        default=Path(tempfile.gettempdir()) / 'civicpulse-security-reports')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    passed = True
    for index, image in enumerate(args.images, 1):
        try:
            # Evaluate every image even when a previous one failed.
            success = scan(image, index, output)
        except (subprocess.CalledProcessError, OSError, ValueError) as error:
            print(f'FAIL: {image}: {type(error).__name__}: {error}', flush=True)
            success = False
        passed = success and passed
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
