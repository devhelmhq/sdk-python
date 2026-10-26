"""Tests for the include-set bundler (``devhelm._bundle``, doc 32 D-12)."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import shutil
import struct
import subprocess
import unicodedata
import zipfile
from pathlib import Path
from typing import Any

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


def test_include_globs_add_to_default_set(tmp_path: Path) -> None:
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
    # The entry directory always ships; include adds files nothing imports,
    # and those are named to the server.
    assert set(bundle.files) == {
        "checks/web/a.spec.ts",
        "checks/web/sibling.ts",
        "checks/api/b.ts",
        "shared/util.ts",
    }
    assert bundle.include == (
        "checks/api/b.ts",
        "checks/web/a.spec.ts",
        "checks/web/sibling.ts",
        "shared/util.ts",
    )


def test_include_ships_fixture_nothing_imports(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    entry = _write(tmp_path, "checks/order.spec.ts")
    _write(tmp_path, "fixtures/order.json", "{}")
    _write(tmp_path, "fixtures/unused.json", "{}")
    bundle = collect({"entrypoint": str(entry), "include": ["fixtures/order.json"]})
    assert set(bundle.files) == {"checks/order.spec.ts", "fixtures/order.json"}
    assert bundle.include == ("fixtures/order.json",)


def test_in_memory_include_must_name_a_file() -> None:
    files = {"a.spec.ts": "x", "fixtures/order.json": "{}"}
    bundle = collect(
        FilesCode(entrypoint="a.spec.ts", files=files, include=["fixtures/order.json"])
    )
    assert bundle.include == ("fixtures/order.json",)
    with pytest.raises(DevhelmApiError):
        collect(FilesCode(entrypoint="a.spec.ts", files=files, include=["nope.json"]))


def test_setup_file_always_included(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    entry = _write(tmp_path, "checks/a.spec.ts")
    _write(tmp_path, "checks/auth.setup.ts")
    _write(tmp_path, "checks/other.ts")
    _write(tmp_path, "other/x.ts")
    bundle = collect({"entrypoint": str(entry), "include": ["nothing/*.ts"]})
    assert "checks/auth.setup.ts" in bundle.files
    assert "other/x.ts" not in bundle.files


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


# -- conformance vectors (mono docs/contracts/bundle-vectors.json, W0-9) ----------
#
# Each vector is {name, request: {entrypoint?, files, binaryFiles?, symlinks?},
# expect: {entrypoint, digest, uploadDigest, files} | {refusal: {code}}}.
# The Python SDK is an include-set client: it hashes what it sends
# (``uploadDigest``) and the server resolves the closure (``digest`` over
# ``expect.files``). Both are recomputed here from the request.


def _load_vectors() -> list[dict[str, Any]]:
    data = json.loads(VECTORS.read_text())
    vectors: list[dict[str, Any]] = data["vectors"]
    assert vectors, "bundle-vectors.json has no vectors"
    return vectors


def _request_files(request: dict[str, Any]) -> dict[str, bytes]:
    files = {p: str(t).encode("utf-8") for p, t in request.get("files", {}).items()}
    for path, b64 in request.get("binaryFiles", {}).items():
        files[path] = base64.b64decode(b64)
    return {normalize_path(p): c for p, c in files.items()}


VECTOR_IDS = [v["name"] for v in _load_vectors()]


@pytest.mark.parametrize("vector", _load_vectors(), ids=VECTOR_IDS)
def test_conformance_vector(vector: dict[str, Any], tmp_path: Path) -> None:
    request, expect = vector["request"], vector["expect"]
    if "refusal" in expect:
        code = expect["refusal"]["code"]
        if request.get("symlinks"):
            for path, content in request.get("files", {}).items():
                _write(tmp_path, path, content)
            for link, target in request["symlinks"].items():
                (tmp_path / link).parent.mkdir(parents=True, exist_ok=True)
                os.symlink(target, tmp_path / link)
            entry = tmp_path / next(iter(request["files"]))
            with pytest.raises(DevhelmApiError) as err:
                collect(entry, root=tmp_path)
            assert err.value.code == code
            field = expect["refusal"].get("field")
            if field is not None:
                assert err.value.errors[0].field == field
        elif request.get("include"):
            # An include path that is not one of the files.
            texts = dict(request["files"])
            with pytest.raises(DevhelmApiError) as err:
                collect(
                    FilesCode(
                        entrypoint=request["entrypoint"],
                        files=texts,
                        include=request["include"],
                    )
                )
            assert err.value.code == code
            assert err.value.errors[0].field == expect["refusal"].get("field")
        else:
            # An import outside the set is found by the server's resolver;
            # the include-set client never parses imports (doc 42 §5.3).
            assert code == "IMPORT_NOT_IN_BUNDLE"
        return
    files = _request_files(request)
    assert bundle_digest(files) == expect["uploadDigest"]
    closure = {p: files[normalize_path(p)] for p in expect["files"]}
    assert bundle_digest(closure) == expect["digest"]
    # The in-memory code form uploads exactly these files.
    entry = request.get("entrypoint") or expect["entrypoint"] or next(iter(files))
    texts = {p: c for p, c in files.items()}
    code = FilesCode(entrypoint=entry, files=texts)
    if request.get("include"):
        code["include"] = list(request["include"])
    bundle = collect(code)
    assert bundle.digest == expect["uploadDigest"]
    assert bundle.include == tuple(request.get("include", []))


def test_include_glob_outside_root_is_refused(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    entry = tmp_path / "checks" / "a.spec.ts"
    entry.parent.mkdir()
    entry.write_text("x")
    with pytest.raises(DevhelmApiError) as err:
        collect({"entrypoint": str(entry), "include": ["../*.ts"]})
    assert err.value.code == "IMPORT_NOT_IN_BUNDLE"


def test_remote_credentials_are_dropped() -> None:
    from devhelm._bundle.source import _public_remote

    assert (
        _public_remote("https://user:tok@github.com/acme/web.git")
        == "https://github.com/acme/web.git"
    )
    assert (
        _public_remote("git@github.com:acme/web.git") == "git@github.com:acme/web.git"
    )
    assert _public_remote(None) is None
