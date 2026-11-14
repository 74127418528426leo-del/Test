#!/usr/bin/env python3
"""Restore the source packages from the four downloaded Debian source ZIPs."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import zipfile

release_dir = Path(sys.argv[1]).resolve()
destination = Path(sys.argv[2]).resolve()
index = json.loads((release_dir / 'SOURCE_INDEX.json').read_text())
details = json.loads((release_dir / 'SOURCE_FILE_DETAILS.json').read_text())
files = {row['sha1']: row for row in details['files']}
destination.mkdir(parents=True, exist_ok=True)
blob_dir = destination / '.verified-blobs'
blob_dir.mkdir(exist_ok=True)
seen = set()
for part in range(1, 5):
    archive = release_dir / f'Puppy50_Debian_Sources_Part_{part:02}.zip'
    with zipfile.ZipFile(archive) as z:
        for member in z.infolist():
            digest = member.filename.removeprefix('blobs/')
            if member.filename != 'blobs/' + digest or digest not in files or digest in seen:
                raise ValueError('Unexpected archive member: ' + member.filename)
            row = files[digest]
            sha1, sha256 = hashlib.sha1(), hashlib.sha256()
            path = blob_dir / digest
            with z.open(member) as src, path.open('wb') as dst:
                while True:
                    chunk = src.read(1024 * 1024)
                    if not chunk:
                        break
                    dst.write(chunk)
                    sha1.update(chunk)
                    sha256.update(chunk)
            if (path.stat().st_size != row['bytes'] or sha1.hexdigest() != digest or
                    sha256.hexdigest() != row['sha256']):
                raise ValueError('Source verification failed: ' + digest)
            seen.add(digest)
if seen != set(files):
    raise ValueError('Some indexed source blobs are missing')
for row in index['source_packages']:
    dirname = (row['source'] + '_' + row['version']).replace('/', '_')
    directory = destination / dirname
    directory.mkdir(exist_ok=True)
    for url in row['source_files']:
        digest = url.rsplit('/', 1)[-1]
        for name in files[digest]['names']:
            if Path(name).name != name:
                raise ValueError('Unsafe source filename: ' + name)
            path = directory / name
            if path.exists():
                if os.stat(path).st_ino != os.stat(blob_dir / digest).st_ino:
                    raise ValueError('Conflicting source name: ' + str(path))
                continue
            try:
                os.link(blob_dir / digest, path)
            except OSError:
                shutil.copyfile(blob_dir / digest, path)
print('Restored', len(index['source_packages']), 'source package versions into', destination)
