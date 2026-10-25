"""Tests for the include-set bundler (``devhelm._bundle``, doc 32 D-12)."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import shutil
import struct
import subprocess
import unicodedata
import zipfile
from pathlib import Path

import pytest

from devhelm._bundle import (
    MAX_FILES,
    FilesCode,
    bundle_digest,
    collect,
    detect_source,
    normalize_path,
)
from devhelm._errors import DevhelmApiError

ROOT = Path(__file__).resolve().parent.parent
VECTORS = ROOT / "docs" / "contracts" / "bundle-vectors.json"
TEXT = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".json", ".yml", ".yaml")
TEXT += (".md", ".txt", ".html", ".css")


def _expected_digest(files: dict[str, bytes]) -> str:
    """An independent D-12 implementation to check ``bundle_digest`` against."""
    h = hashlib.sha256()
    for path in sorted(files, key=lambda p: p.encode("utf-8")):
        content = files[path]
        if path.lower().endswith(TEXT):
            content = content.replace(b"\r\n", b"\n")
        raw = path.encode("utf-8")
        h.update(struct.pack(">I", len(raw)) + raw)
        h.update(struct.pack(">Q", len(content)) + content)
    return "sha256:" + h.hexdigest()


def _code(err: pytest.ExceptionInfo[DevhelmApiError]) -> str:
    return err.value.code


# -- digest ---------------------------------------------------------------------


def test_digest_matches_independent_framing() -> None:
    files = {"a.ts": b"export {}\n", "lib/util.ts": b"x", "data.json": b"{}"}
    assert bundle_digest(files) == _expected_digest(files)


def test_digest_orders_by_utf8_bytes() -> None:
    files = {"a.ts": b"1", "B.ts": b"2", "é.ts": b"3", "z/a.ts": b"4"}
    assert bundle_digest(files) == _expected_digest(files)
    # Order of the input mapping never matters.
    assert bundle_digest(dict(reversed(list(files.items())))) == bundle_digest(files)


def test_digest_normalizes_crlf_only_for_text_extensions() -> None:
    assert bundle_digest({"a.ts": b"x\r\ny\r\n"}) == bundle_digest({"a.ts": b"x\ny\n"})
    assert bundle_digest({"A.JSON": b"{\r\n}"}) == bundle_digest({"A.JSON": b"{\n}"})
    assert bundle_digest({"img.png": b"x\r\n"}) != bundle_digest({"img.png": b"x\n"})


def test_digest_of_empty_map_is_sha256_of_nothing() -> None:
    assert bundle_digest({}) == "sha256:" + hashlib.sha256(b"").hexdigest()


def test_digest_framing_separates_path_and_content() -> None:
    assert bundle_digest({"ab": b"c"}) != bundle_digest({"a": b"bc"})


# -- paths ----------------------------------------------------------------------


def test_normalize_path_strips_prefix_and_backslashes() -> None:
    assert normalize_path("./././a/b.ts") == "a/b.ts"
    assert normalize_path("a\\b\\c.ts") == "a/b/c.ts"


def test_normalize_path_is_nfc() -> None:
    decomposed = unicodedata.normalize("NFD", "café.ts")
    assert decomposed != "café.ts"
    assert normalize_path(decomposed) == unicodedata.normalize("NFC", "café.ts")


@pytest.mark.parametrize(
    "raw", ["/abs.ts", "a/../b.ts", "..", "a//b.ts", "", ".env", "a/.hidden/x.ts"]
)
def test_normalize_path_refusals(raw: str) -> None:
    with pytest.raises(DevhelmApiError) as err:
        normalize_path(raw)
    assert _code(err) == "MONITOR_PACKAGE_PATH_INVALID"
    assert err.value.category == "validation"
    assert err.value.status == 0


# -- in memory ------------------------------------------------------------------


def test_collect_in_memory_str_and_bytes() -> None:
    code: FilesCode = {
        "entrypoint": "./checkout.spec.ts",
        "files": {"checkout.spec.ts": "test()\r\n", "./logo.png": b"\x89PNG\x00"},
    }
    bundle = collect(code)
    assert bundle.entrypoint == "checkout.spec.ts"
    assert bundle.files == {
        "checkout.spec.ts": b"test()\r\n",
        "logo.png": b"\x89PNG\x00",
    }
    assert bundle.digest == bundle_digest(bundle.files)
    assert bundle.digest == _expected_digest(bundle.files)
    assert bundle.root is None and bundle.source is None
    assert bundle.size == len(b"test()\r\n") + 5


def test_in_memory_digest_is_stable_across_str_and_bytes() -> None:
    a = collect({"entrypoint": "a.ts", "files": {"a.ts": "é"}})
    b = collect({"entrypoint": "a.ts", "files": {"a.ts": "é".encode()}})
    assert a.digest == b.digest


def test_in_memory_entrypoint_must_be_a_file() -> None:
    with pytest.raises(DevhelmApiError) as err:
        collect({"entrypoint": "missing.ts", "files": {"a.ts": "x"}})
    assert _code(err) == "MONITOR_PACKAGE_PATH_INVALID"


def test_in_memory_duplicate_after_normalization_refused() -> None:
    with pytest.raises(DevhelmApiError):
        collect({"entrypoint": "a.ts", "files": {"a.ts": "x", "./a.ts": "y"}})


def test_as_text_and_as_zip() -> None:
    text = collect({"entrypoint": "a.ts", "files": {"a.ts": "x", "b.json": "{}"}})
    assert text.as_text() == {"a.ts": "x", "b.json": "{}"}
    binary = collect(
        {"entrypoint": "a.ts", "files": {"a.ts": "x", "img.png": b"\xff\xfe\x00"}}
    )
    assert binary.as_text() is None
    with zipfile.ZipFile(io.BytesIO(binary.as_zip())) as zf:
        assert sorted(zf.namelist()) == ["a.ts", "img.png"]
        assert zf.read("img.png") == b"\xff\xfe\x00"


# -- from disk --------------------------------------------------------------------


def _write(root: Path, rel: str, content: bytes | str = "x") -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content.encode() if isinstance(content, str) else content)
    return path


def test_root_is_nearest_git_ancestor(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    entry = _write(tmp_path, "checks/web/checkout.spec.ts")
    _write(tmp_path, "checks/web/helper.ts")
    _write(tmp_path, "other/far.ts")
    bundle = collect(str(entry))
    assert bundle.root == tmp_path.resolve()
    assert bundle.entrypoint == "checks/web/checkout.spec.ts"
    assert set(bundle.files) == {"checks/web/checkout.spec.ts", "checks/web/helper.ts"}


def test_root_defaults_to_entry_dir(tmp_path: Path) -> None:
    entry = _write(tmp_path, "proj/a.spec.ts")
    bundle = collect(entry)
    assert bundle.root == (tmp_path / "proj").resolve()
    assert bundle.entrypoint == "a.spec.ts"


def test_explicit_root(tmp_path: Path) -> None:
    entry = _write(tmp_path, "proj/sub/a.spec.ts")
    bundle = collect(entry, root=tmp_path / "proj")
    assert bundle.entrypoint == "sub/a.spec.ts"
    assert set(bundle.files) == {"sub/a.spec.ts"}


def test_default_include_set_exclusions(tmp_path: Path) -> None:
    entry = _write(tmp_path, "a.spec.ts")
    _write(tmp_path, "lib/util.ts")
    _write(tmp_path, "data.json")
    for rel in [
        "node_modules/pkg/index.js",
        "dist/out.js",
        "build/out.js",
        "coverage/lcov.info",
        "a.spec.ts.map",
        ".env",
        ".env.local",
        ".hidden.ts",
        ".github/workflows/ci.yml",
        "lib/node_modules/x.js",
    ]:
        _write(tmp_path, rel)
    bundle = collect(entry)
    assert set(bundle.files) == {"a.spec.ts", "lib/util.ts", "data.json"}


def test_devhelmignore_patterns(tmp_path: Path) -> None:
    entry = _write(tmp_path, "a.spec.ts")
    _write(
        tmp_path,
        ".devhelmignore",
        "# comment\n/root-only.ts\nscratch.ts\nfixtures/\n*.json\n!keep.json\n"
        "deep/**/gen.ts\n",
    )
    for rel in [
        "root-only.ts",
        "lib/root-only.ts",
        "scratch.ts",
        "lib/scratch.ts",
        "fixtures/a.ts",
        "lib/fixtures/b.ts",
        "data.json",
        "keep.json",
        "deep/x/y/gen.ts",
        "deep/gen.ts",
        "deep/keep.ts",
    ]:
        _write(tmp_path, rel)
    bundle = collect(entry)
    assert set(bundle.files) == {
        "a.spec.ts",
        "lib/root-only.ts",  # anchored pattern only matches at the root
        "keep.json",  # negation re-includes
        "deep/keep.ts",
    }


def test_devhelmignore_in_entry_dir_is_relative_to_it(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    entry = _write(tmp_path, "checks/a.spec.ts")
    _write(tmp_path, "checks/.devhelmignore", "/local.ts\n")
    _write(tmp_path, "checks/local.ts")
    _write(tmp_path, "checks/sub/local.ts")
    bundle = collect(entry)
    assert set(bundle.files) == {"checks/a.spec.ts", "checks/sub/local.ts"}


def test_include_globs_replace_default_set(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    entry = _write(tmp_path, "checks/web/a.spec.ts")
    _write(tmp_path, "checks/web/sibling.ts")
    _write(tmp_path, "checks/api/b.ts")
    _write(tmp_path, "checks/api/b.json")
    _write(tmp_path, "shared/util.ts")
    _write(tmp_path, "shared/other.ts")
    _write(tmp_path, "checks/node_modules/x.ts")
    bundle = collect(
        {"entrypoint": str(entry), "include": ["checks/**/*.ts", "./shared/util.ts"]}
    )
    assert set(bundle.files) == {
        "checks/web/a.spec.ts",
        "checks/web/sibling.ts",
        "checks/api/b.ts",
        "shared/util.ts",
    }


def test_setup_file_always_included(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    entry = _write(tmp_path, "checks/a.spec.ts")
    _write(tmp_path, "checks/auth.setup.ts")
    _write(tmp_path, "checks/other.ts")
    bundle = collect({"entrypoint": str(entry), "include": ["nothing/*.ts"]})
    assert set(bundle.files) == {"checks/a.spec.ts", "checks/auth.setup.ts"}


def test_custom_setup_file(tmp_path: Path) -> None:
    entry = _write(tmp_path, "a.spec.ts")
    _write(tmp_path, "login.setup.ts")
    bundle = collect(
        {"entrypoint": str(entry), "include": []}, setup_file="login.setup.ts"
    )
    assert set(bundle.files) == {"a.spec.ts", "login.setup.ts"}


def test_entry_symlink_refused(tmp_path: Path) -> None:
    target = _write(tmp_path, "real.spec.ts")
    link = tmp_path / "link.spec.ts"
    link.symlink_to(target)
    with pytest.raises(DevhelmApiError) as err:
        collect(link)
    assert _code(err) == "MONITOR_PACKAGE_PATH_INVALID"


def test_symlink_inside_set_refused(tmp_path: Path) -> None:
    entry = _write(tmp_path, "proj/a.spec.ts")
    outside = _write(tmp_path, "secret.ts")
    (tmp_path / "proj" / "shared.ts").symlink_to(outside)
    with pytest.raises(DevhelmApiError) as err:
        collect(entry)
    assert _code(err) == "MONITOR_PACKAGE_PATH_INVALID"
    assert "symlink" in err.value.message


def test_symlinked_dir_inside_set_refused(tmp_path: Path) -> None:
    entry = _write(tmp_path, "proj/a.spec.ts")
    _write(tmp_path, "lib/x.ts")
    (tmp_path / "proj" / "lib").symlink_to(tmp_path / "lib", target_is_directory=True)
    with pytest.raises(DevhelmApiError) as err:
        collect(entry)
    assert _code(err) == "MONITOR_PACKAGE_PATH_INVALID"


def test_too_many_files(tmp_path: Path) -> None:
    entry = _write(tmp_path, "a.spec.ts")
    for i in range(MAX_FILES):
        _write(tmp_path, f"many/f{i}.ts", "12")
    with pytest.raises(DevhelmApiError) as err:
        collect(entry)
    assert _code(err) == "BUNDLE_TOO_LARGE"
    details = err.value.details
    assert details is not None
    assert details["files"] == MAX_FILES + 1
    assert details["bytes"] == MAX_FILES * 2 + 1
    largest = details["largestDirectories"]
    assert isinstance(largest, list)
    assert largest[0] == {"dir": "many", "bytes": MAX_FILES * 2}


def test_entry_outside_root(tmp_path: Path) -> None:
    entry = _write(tmp_path, "elsewhere/a.spec.ts")
    (tmp_path / "root").mkdir()
    with pytest.raises(DevhelmApiError) as err:
        collect(entry, root=tmp_path / "root")
    assert _code(err) == "IMPORT_NOT_IN_BUNDLE"


def test_missing_entry(tmp_path: Path) -> None:
    with pytest.raises(DevhelmApiError) as err:
        collect(tmp_path / "nope.spec.ts")
    assert _code(err) == "MONITOR_PACKAGE_PATH_INVALID"


def test_disk_digest_matches_in_memory(tmp_path: Path) -> None:
    entry = _write(tmp_path, "a.spec.ts", "x\r\n")
    _write(tmp_path, "lib/u.ts", "y")
    disk = collect(entry)
    memory = collect(
        {"entrypoint": "a.spec.ts", "files": {"a.spec.ts": "x\r\n", "lib/u.ts": "y"}}
    )
    assert disk.digest == memory.digest


# -- source -------------------------------------------------------------------


def test_detect_source_from_ci_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GITHUB_REPOSITORY", "acme/web")
    monkeypatch.setenv("GITHUB_REF_NAME", "main")
    monkeypatch.setenv("GITHUB_SHA", "abc123")
    monkeypatch.delenv("GITHUB_HEAD_REF", raising=False)
    entry = _write(tmp_path, "checks/a.spec.ts")
    source = detect_source(entry, tmp_path)
    assert source is not None
    assert (source.repo, source.branch, source.commit) == ("acme/web", "main", "abc123")
    assert source.file == "checks/a.spec.ts"


def test_detect_source_prefers_head_ref(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GITHUB_REPOSITORY", "acme/web")
    monkeypatch.setenv("GITHUB_SHA", "abc")
    monkeypatch.setenv("GITHUB_REF_NAME", "123/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", "feature")
    source = detect_source(None, None)
    assert source is not None and source.branch == "feature"


def test_detect_source_none_without_env_or_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for key in (
        "GITHUB_REPOSITORY",
        "GITHUB_REF_NAME",
        "GITHUB_SHA",
        "GITHUB_HEAD_REF",
    ):
        monkeypatch.delenv(key, raising=False)
    assert detect_source(None, None) is None


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_detect_source_from_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for key in (
        "GITHUB_REPOSITORY",
        "GITHUB_REF_NAME",
        "GITHUB_SHA",
        "GITHUB_HEAD_REF",
    ):
        monkeypatch.delenv(key, raising=False)
    env = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.com",
        "HOME": str(tmp_path),
        "PATH": __import__("os").environ["PATH"],
    }

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", *args],
            cwd=tmp_path,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    git("init", "-q", "-b", "trunk")
    git("remote", "add", "origin", "https://github.com/acme/web.git")
    entry = _write(tmp_path, "checks/a.spec.ts")
    git("add", ".")
    git("commit", "-q", "-m", "init")
    sha = git("rev-parse", "HEAD")
    bundle = collect(entry)
    assert bundle.source is not None
    assert bundle.source.repo == "https://github.com/acme/web.git"
    assert bundle.source.branch == "trunk"
    assert bundle.source.commit == sha
    assert bundle.source.file == "checks/a.spec.ts"


# -- conformance vectors (mono docs/contracts/bundle-vectors.json, Wave 0) ---------


def _vector_files(raw: dict[str, object]) -> dict[str, bytes]:
    """A vector's file map: ``path -> str | {"utf8": str} | {"base64": str}``."""
    out: dict[str, bytes] = {}
    for path, value in raw.items():
        if isinstance(value, str):
            out[path] = value.encode("utf-8")
        elif isinstance(value, dict) and "base64" in value:
            out[path] = base64.b64decode(str(value["base64"]))
        elif isinstance(value, dict) and "utf8" in value:
            out[path] = str(value["utf8"]).encode("utf-8")
        else:
            raise AssertionError(f"unrecognised file encoding for {path!r}: {value!r}")
    return out


def _load_vectors() -> list[dict[str, object]]:
    """``{"vectors": [...]}`` or a bare list; each vector is a dict."""
    if not VECTORS.exists():
        pytest.skip(
            "docs/contracts/bundle-vectors.json not vendored yet (mono Wave 0, W0-9)"
        )
    data = json.loads(VECTORS.read_text())
    vectors = data.get("vectors", []) if isinstance(data, dict) else data
    assert isinstance(vectors, list) and vectors, "bundle-vectors.json has no vectors"
    return [v for v in vectors if isinstance(v, dict)]


def test_conformance_vectors() -> None:
    checked = 0
    for vector in _load_vectors():
        name = vector.get("name", "?")
        raw_files = vector.get("files")
        expect = vector.get("expect") or vector.get("expected") or {}
        if not isinstance(raw_files, dict) or not isinstance(expect, dict):
            continue
        files = {normalize_path(p): c for p, c in _vector_files(raw_files).items()}
        # The include-set client only computes the digest of what it sends,
        # so it checks ``uploadDigest`` (or ``digest`` when the vector's
        # files are already the closure: no ``entrypoint`` / ``include``).
        upload = expect.get("uploadDigest")
        closure_only = "entrypoint" not in vector and "include" not in vector
        target = upload or (expect.get("digest") if closure_only else None)
        if isinstance(target, str):
            assert bundle_digest(files) == target, f"vector {name}"
            checked += 1
    assert checked, "no vector carried a digest the Python client can check"
