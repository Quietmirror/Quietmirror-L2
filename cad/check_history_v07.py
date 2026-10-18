"""Verify V0.1--V0.6 assets against the published V0.6 Git snapshot."""
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = '6c43049426fdda54379b73b59314773750b6ce1b'
ALLOWED = {'README.md', 'HISTORY.md'}

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])

rows = []
for record in git('ls-tree', '-r', '-z', BASE).decode('utf8').split('\0'):
    if not record:
        continue
    meta, path = record.split('\t')
    if path in ALLOWED:
        continue
    expected = meta.split()[2]
    file = ROOT / path
    assert file.is_file(), f'Missing historical asset: {path}'
    actual = git('hash-object', '--path=' + path, str(file)).decode().strip()
    assert actual == expected, f'Historical asset changed: {path}'
    rows.append({'path': path, 'unchanged': True})

old_readme = git('show', BASE + ':README.md')
assert (ROOT / 'README_V0.6.md').read_bytes() == old_readme
report = {
    'baseline_commit': BASE,
    'unchanged_previous_files': len(rows),
    'verified_files': rows,
    'allowed_index_updates': sorted(ALLOWED),
    'readme_v06_exact_byte_archive': True,
    'note': 'All earlier models, source, parameters, images, reports and profiles retained. Only the shared README and HISTORY index are updated.'
}
dest = ROOT / 'reports/v07/history_preservation.json'
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps(report, indent=2), encoding='utf8')
print(f'{len(rows)} previous files unchanged; V0.6 README archive byte-identical.')
