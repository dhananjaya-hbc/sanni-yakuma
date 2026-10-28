from datetime import UTC, datetime

from sanni_yakuma.detectors import amukku, bihiri, golu, gulma, jala, kana, kora, pith, read_omens, slesma

LONG_README = "# Demo\n\n" + "word " * 200
HEALTHY = {
    "README.md": LONG_README,
    "LICENSE": "MIT License",
    ".gitignore": ".env\n",
    ".github/workflows/ci.yml": "on: push",
    "app/core.py": 'def add(a, b):\n    """Add."""\n    return a + b\n',
    "tests/test_core.py": "def test_add():\n    assert True\n",
}


def test_healthy_repo_has_no_demons(make_repo):
    omens = read_omens(make_repo(HEALTHY))
    assert [o.demon for o in omens if o.found] == []


# Golu: silent repo
def test_golu_no_readme(make_repo):
    omen = golu.detect(make_repo({"a.py": "x = 1\n"}))
    assert omen.found and omen.severity_hint == 3


def test_golu_thin_readme(make_repo):
    omen = golu.detect(make_repo({"README.md": "hello world"}))
    assert omen.severity_hint == 2 and omen.metrics["readme_words"] == 2


# Kana: no tests
def test_kana_no_tests(make_repo):
    omen = kana.detect(make_repo({f"src/m{i}.py": "x = 1\n" for i in range(4)}))
    assert omen.found and omen.severity_hint == 3


def test_kana_test_patterns(make_repo):
    repo = make_repo({"a.js": "", "a.test.js": "", "b_test.go": "", "FooTest.java": "", "__tests__/x.ts": ""})
    assert len(repo.test_files) == 4 and repo.source_files == ["a.js"]


# Jala: no CI
def test_jala_no_ci(make_repo):
    assert jala.detect(make_repo({"a.py": ""})).found


def test_jala_gitlab_ci(make_repo):
    assert not jala.detect(make_repo({".gitlab-ci.yml": "x"})).found


# Pith: no license
def test_pith_no_license(make_repo):
    assert pith.detect(make_repo({"a.py": ""})).severity_hint == 3


def test_pith_declared_only(make_repo):
    omen = pith.detect(make_repo({"package.json": '{"license": "MIT"}'}))
    assert omen.severity_hint == 1 and omen.metrics["declared_license"] == "MIT"


# Gulma: worms
def test_gulma_counts_comment_markers_only(make_repo):
    code = "# TODO: one\n// FIXME two\nx = 'TODO not a comment'\n" * 3
    omen = gulma.detect(make_repo({"a.py": code}))
    assert omen.metrics["total"] == 6 and omen.metrics["todo"] == 3 and omen.found


# Bihiri: swallowed errors
def test_bihiri_python(make_repo):
    code = (
        "try:\n    x()\nexcept:\n    y()\n"           # bare except
        "try:\n    x()\nexcept ValueError:\n    pass\n"  # silenced
        "try:\n    import ujson\nexcept ImportError:\n    pass\n"  # optional import: fine
    )
    omen = bihiri.detect(make_repo({"a.py": code}))
    assert omen.metrics["total"] == 2 and omen.metrics["bare_except"] == 1


def test_bihiri_js(make_repo):
    code = "try { a() } catch (e) {}\np.catch(() => {})\ntry {\n} catch (err) {\n}\ntry { a() } catch (e) { log(e) }\n"
    assert bihiri.detect(make_repo({"a.js": code})).metrics["total"] == 3


# Amukku: log vomit
def test_amukku_needs_count_and_density(make_repo):
    noisy = "console.log(1)\n" * 30 + "x()\n" * 70
    assert amukku.detect(make_repo({"src/a.js": noisy})).severity_hint == 2


def test_amukku_ignores_cli_files(make_repo):
    assert not amukku.detect(make_repo({"cli.py": "print(1)\n" * 50})).found


# Kora: paralysis
def test_kora_old_repo(make_repo):
    repo = make_repo({"a.py": ""}, commit_date="2023-01-01T00:00:00+00:00")
    omen = kora.detect(repo, now=datetime(2026, 10, 28, tzinfo=UTC))
    assert omen.severity_hint == 3 and omen.metrics["months_since"] > 40


def test_kora_archived(make_repo):
    repo = make_repo({"a.py": ""})
    repo.meta = {"archived": True}
    assert kora.detect(repo, now=datetime(2026, 10, 28, tzinfo=UTC)).severity_hint == 3


# Slesma: clogged repo
def test_slesma_node_modules_and_env(make_repo):
    omen = slesma.detect(make_repo({
        ".gitignore": "", "node_modules/x/index.js": "", ".env": "KEY=1", "app.exe": b"\0\1",
    }))
    assert omen.severity_hint == 3
    assert omen.metrics["junk_dirs"] == 1 and omen.metrics["binaries"] == 1


def test_slesma_no_gitignore(make_repo):
    assert slesma.detect(make_repo({"a.py": ""})).severity_hint == 1
