#!/bin/sh
set -eu
cd "$(dirname "$0")"
python3 tools/reader_build.py
mkdir -p dist
cp site/downloads/k8s-book-reader.epub dist/从零开始学Kubernetes.epub
cp site/downloads/k8s-book-reader.html dist/从零开始学Kubernetes.html
python3 - <<'PYZIP'
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
with ZipFile('dist/Kubernetes零基础学习包.zip', 'w', ZIP_DEFLATED) as archive:
    for path in [Path('dist/从零开始学Kubernetes.epub'), Path('dist/从零开始学Kubernetes.html'), Path('src/book.md')]:
        archive.write(path, path.name)
    for folder in ['examples', 'lab']:
        for path in Path(folder).rglob('*'):
            if path.is_file() and path.suffix in {'.yaml', '.py', '.sh'}:
                archive.write(path, str(path))
PYZIP
