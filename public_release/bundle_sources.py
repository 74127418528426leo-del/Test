#!/usr/bin/env python3
"""Mirror indexed Debian Snapshot source files into bounded release ZIPs.

Files are identified and checked by the SHA-1 identifiers used by Debian
Snapshot. SHA-256 values are also recorded for end-user integrity checking.
"""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
import urllib.request
import zipfile

index_path, output_path = map(Path, sys.argv[1:3])
index = json.loads(index_path.read_text())
if any('error' in row for row in index['source_packages']):
    raise SystemExit('Source inventory has unresolved packages')
urls = sorted({url for row in index['source_packages'] for url in row['source_files']})
if not urls:
    raise SystemExit('Empty source inventory')
output_path.mkdir(parents=True, exist_ok=True)
blobs = output_path / 'source_blobs'
blobs.mkdir(exist_ok=True)


def request(url):
    return urllib.request.urlopen(urllib.request.Request(
        url, headers={'User-Agent': 'Puppy50-public-preview-source-archive/1.0'}), timeout=90)


def get_metadata(url):
    digest = url.rsplit('/', 1)[-1]
    if not re.fullmatch(r'[0-9a-f]{40}', digest):
        raise ValueError('Unexpected snapshot identifier: ' + digest)
    for attempt in range(6):
        try:
            with request('https://snapshot.debian.org/mr/file/' + digest + '/info') as response:
                rows = json.load(response)['result']
            sizes = {row['size'] for row in rows}
            names = sorted({row['name'] for row in rows})
            if len(sizes) != 1 or not names or any(Path(n).name != n for n in names):
                raise ValueError('Invalid snapshot file metadata for ' + digest)
            return {'sha1': digest, 'url': url, 'bytes': sizes.pop(), 'names': names}
        except Exception:
            if attempt == 5:
                raise
            time.sleep(min(20, 1.5 * (attempt + 1)))


def download(row):
    path = blobs / row['sha1']
    tmp = path.with_suffix('.part')
    for attempt in range(6):
        try:
            sha1, sha256, size = hashlib.sha1(), hashlib.sha256(), 0
            with request(row['url']) as response, tmp.open('wb') as out:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
                    sha1.update(chunk)
                    sha256.update(chunk)
                    size += len(chunk)
            if sha1.hexdigest() != row['sha1'] or size != row['bytes']:
                raise ValueError('Source file hash or size mismatch: ' + row['sha1'])
            os.replace(tmp, path)
            row['sha256'] = sha256.hexdigest()
            return row
        except Exception:
            tmp.unlink(missing_ok=True)
            if attempt == 5:
                raise
            time.sleep(min(30, 2 * (attempt + 1)))


def run_parallel(func, items, workers, description):
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(func, item) for item in items]
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            results.append(future.result())
            if i % 50 == 0 or i == len(futures):
                print(description, i, '/', len(futures), flush=True)
    return results


rows = run_parallel(get_metadata, urls, 16, 'source metadata')
by_digest = {row['sha1']: row for row in rows}
for package in index['source_packages']:
    names = {}
    for url in package['source_files']:
        digest = url.rsplit('/', 1)[-1]
        for name in by_digest[digest]['names']:
            if name in names and names[name] != digest:
                raise ValueError('Conflicting names in source package: ' + package['source'] + '/' + name)
            names[name] = digest
rows = run_parallel(download, rows, 8, 'source downloads')
rows.sort(key=lambda row: row['sha1'])
manifest = {'format': 1, 'files': rows, 'count': len(rows),
            'total_bytes': sum(row['bytes'] for row in rows)}
(output_path / 'SOURCE_FILE_DETAILS.json').write_text(json.dumps(manifest, indent=2) + '\n')

# Greedy balancing keeps every release asset under GitHub's 2 GB asset limit.
parts = [([], 0) for _ in range(4)]
for row in sorted(rows, key=lambda r: r['bytes'], reverse=True):
    idx = min(range(len(parts)), key=lambda i: parts[i][1])
    entries, size = parts[idx]
    entries.append(row)
    parts[idx] = (entries, size + row['bytes'])
for number, (entries, size) in enumerate(parts, 1):
    if size >= 1_800_000_000:
        raise ValueError('Source part too large: ' + str(size))
    archive = output_path / f'Puppy50_Debian_Sources_Part_{number:02}.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_STORED, allowZip64=True) as z:
        for row in entries:
            z.write(blobs / row['sha1'], 'blobs/' + row['sha1'])
            (blobs / row['sha1']).unlink()
    with zipfile.ZipFile(archive) as z:
        if set(z.namelist()) != {'blobs/' + row['sha1'] for row in entries}:
            raise ValueError('ZIP directory mismatch: ' + str(archive))
    print('Created', archive.name, archive.stat().st_size, 'bytes', flush=True)
shutil.rmtree(blobs)
print('All indexed source files verified and archived.', flush=True)
