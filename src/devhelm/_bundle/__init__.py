"""Collect a check's files for ``POST /bundles`` (doc 42 §5.3, doc 32 D-12).

The Python SDK is an include-set client: it never parses JavaScript or
TypeScript. It sends a set of files and the entrypoint, and the server
resolves the import closure. ``BundleDto.digest`` (the closure digest) is the
revision identity; ``BundleDto.upload_digest`` is the digest of what was
sent, which the SDK recomputes locally and compares.

``code`` takes three forms:

* a path to the entry file (``"./checkout.spec.ts"``);
* ``{"entrypoint": path, "include": [glob, …]}``;
* ``{"entrypoint": "checkout.spec.ts", "files": {path: str | bytes}}``
  (in memory: nothing is read from disk).

For the first two, the bundle root is ``root`` when given, else the nearest
ancestor of the entry file containing ``.git``, else the entry file's
directory. Paths are sent relative to the root. The default include set is
the entry file's directory, recursively, minus ``node_modules/``, ``.git/``,
``dist/``, ``build/``, ``coverage/``, ``*.map``, dotfiles (``.env*``
included) and anything ``.devhelmignore`` (gitignore syntax) matches.
``include`` globs (relative to the root) replace that default. The session
setup file (``auth.setup.ts`` next to the entry file) is always sent when it
exists. Symlinks are refused.
"""

from devhelm._bundle.collect import (
    DEFAULT_SETUP_FILE,
    MAX_BYTES,
    MAX_FILES,
    CodeInput,
    CollectedBundle,
    FilesCode,
    IncludeCode,
    collect,
)
from devhelm._bundle.digest import (
    TEXT_EXTENSIONS,
    bundle_digest,
    normalize_content,
    normalize_path,
)
from devhelm._bundle.ignore import IGNORE_FILE, IgnoreRules
from devhelm._bundle.select import EXCLUDED_DIRS
from devhelm._bundle.source import detect_source

__all__ = [
    "DEFAULT_SETUP_FILE",
    "EXCLUDED_DIRS",
    "IGNORE_FILE",
    "MAX_BYTES",
    "MAX_FILES",
    "TEXT_EXTENSIONS",
    "CodeInput",
    "CollectedBundle",
    "FilesCode",
    "IgnoreRules",
    "IncludeCode",
    "bundle_digest",
    "collect",
    "detect_source",
    "normalize_content",
    "normalize_path",
]
