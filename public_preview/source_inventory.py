#!/usr/bin/env python3
"""Map installed Debian binary packages to exact snapshot source files."""
import concurrent.futures
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def package_sources(status):
    result = {}
    for para in status.split('\n\n'):
        if 'Status: install ok installed' not in para:
            continue
        fields = dict(re.findall(r'(?m)^(Package|Source|Version): (.*)$', para))
        if 'Package' not in fields or 'Version' not in fields:
            continue
        match = re.fullmatch(r'([^ ]+)(?: \(([^)]+)\))?', fields.get('Source', fields['Package']))
        if not match:
            raise ValueError(fields)
        source = match.group(1)
        version = match.group(2) or re.sub(r'\+b\d+$', '', fields['Version'])
        result.setdefault((source, version), []).append((fields['Package'], fields['Version']))
    return result


def resolve(item):
    (source, version), binaries = item
    prefix = 'https://snapshot.debian.org/mr/package/'
    url = prefix + urllib.parse.quote(source, safe='') + '/' + urllib.parse.quote(version, safe='') + '/srcfiles'
    error = ''
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'Puppy50-source-inventory/1.0'})
            with urllib.request.urlopen(request, timeout=25) as response:
                doc = json.load(response)
            hashes = sorted(x['hash'] for x in doc['result'])
            if not hashes:
                raise ValueError('empty source file list')
            return {'source': source, 'version': version, 'binary_packages': binaries,
                    'metadata_url': url, 'source_files': ['https://snapshot.debian.org/file/' + h for h in hashes]}
        except Exception as exc:
            error = repr(exc)
            if isinstance(exc, urllib.error.HTTPError) and exc.code == 404:
                break
            time.sleep(0.5 * (attempt + 1))
    return {'source': source, 'version': version, 'binary_packages': binaries,
            'metadata_url': url, 'error': error}


def main():
    status = Path(sys.argv[1]).read_text(errors='replace')
    output = Path(sys.argv[2])
    sources = package_sources(status)
    # The signed-kernel source contains Debian signing data; include Linux's
    # actual source version separately when the corresponding kernel is installed.
    for (source, _), binaries in list(sources.items()):
        if source == 'linux-signed-amd64':
            for package, binary_version in binaries:
                if package.startswith('linux-image-'):
                    sources.setdefault(('linux', binary_version), [('linux kernel source', binary_version)])
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        rows = list(pool.map(resolve, sorted(sources.items())))
    output.write_text(json.dumps({'format': 1, 'source_packages': rows}, indent=2) + '\n')
    missing = [x for x in rows if 'error' in x]
    print('sources', len(rows), 'resolved', len(rows)-len(missing), 'unresolved', len(missing), flush=True)
    for x in missing:
        print(x['source'], x['version'], x['error'], flush=True)


if __name__ == '__main__':
    main()
