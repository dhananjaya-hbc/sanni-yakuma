# Sanni Yakuma

**An AI exorcism for codebases, after the healing ritual of southern Sri Lanka.**

In the Sanni Yakuma ritual, masked dancers call out the eighteen Sanni demons, each believed to
cause one illness. The demons are questioned, mocked, humbled and sent away. The ritual opens with
blessings, and the leader of the demons, Kola Sanniya, comes last.

This tool performs the same ritual on a GitHub repository. Each demon causes one code sickness.
Plain detectors find the evidence in the code, and an open Gemma model names the demons, gives each
one a short monologue, and writes a concrete cure.

**[Visit the Hall of Masks](https://dhananjaya-hbc.github.io/sanni-yakuma/)** to see rituals
performed on well-known repositories.

## How it works

1. **Summon.** Shallow-clone the repository (or use a local folder).
2. **Read the omens.** Eighteen small detectors, with no AI, collect evidence: file, line, snippet,
   numbers.
3. **Diagnosis.** Gemma reads only that evidence and returns JSON: the blessings (real strengths),
   the demons with severity and evidence ids, a monologue and an exorcism for each, and Kola
   Sanniya's verdict with a short blessing verse in Sinhala.
4. **Keep it honest.** Demons or evidence that the detectors did not find are thrown out. Gemma
   writes each code fix as a find/replace edit; the fix is shown as a diff only if those lines really
   exist in the code.
5. **The ritual page.** One self-contained HTML page: the blessings as oil lamps, then each demon
   with its mask, evidence (linked to the exact commit), monologue and cure.

## The eighteen demons

| Demon | Traditional illness | Code sickness | What the detector looks for |
|---|---|---|---|
| Amukku | vomiting | log vomit | debug prints per 1,000 lines |
| Abutha | madness not caused by spirits | self-made complexity | long, tangled or deeply nested functions |
| Butha | madness caused by spirits | dependency hell | no lockfile, wildcard or unversioned dependencies |
| Bihiri | deafness | swallowed errors | bare `except:`, `except: pass`, empty `catch {}` |
| Deva | epidemics | copy-paste spreading | duplicated blocks across files (build bundles ignored) |
| Gedi | boils, skin disease | style sores | no linter or formatter |
| Gini Jala | malaria, high fever | hotfix fever | share of fix and panic commits |
| Golu | muteness | silent repo | missing or thin README, few docstrings |
| Gulma | worms | hidden worms | TODO, FIXME, HACK, XXX comments |
| Jala | cholera, chills | left in the cold | no CI |
| Kana | blindness | can't see if it works | few or no tests |
| Kora | lameness, paralysis | paralysed repo | months since the last commit, archived, open issues |
| Maru | delirium, death | dead code | blocks of commented-out code |
| Naga | snake nightmares | security nightmares | API keys, private keys, committed `.env` (always masked) |
| Pissu | temporary madness | magic madness | magic numbers, hard-coded paths and local hosts |
| Pith | bile | bitter legal trouble | no license |
| Slesma | phlegm | clogged repo | committed `node_modules`, binaries, huge files, no `.gitignore` |
| Vatha | bloating | dependency bloat | many dependencies for little code, trivial packages |

## Usage

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```sh
git clone https://github.com/dhananjaya-hbc/sanni-yakuma
cd sanni-yakuma
cp .env.example .env          # add your GEMINI_API_KEY from Google AI Studio
uv run sanni ping             # check that Gemma answers

uv run sanni omens https://github.com/request/request      # detectors only, no AI
uv run sanni exorcise https://github.com/request/request   # the full ritual -> out/request-request.html
uv run sanni exorcise . --model gemma-4-31b-it             # a local folder, with the larger model
uv run sanni render out/*.json                             # re-render pages without calling Gemma
uv run sanni gallery out/*.json --out docs                 # build the Hall of Masks
```

### Where Gemma runs

Gemma has open weights, so there is no lock-in. Set `MODEL_PROVIDER` in `.env`:

| `MODEL_PROVIDER` | Where | Needs |
|---|---|---|
| `aistudio` (default) | Google AI Studio, free tier | `GEMINI_API_KEY` |
| `openrouter` | OpenRouter | `OPENROUTER_API_KEY`, `MODEL_NAME` |
| `ollama` | your own laptop or server: your code never leaves it | `OLLAMA_HOST`, `MODEL_NAME` |

## GitHub Action

Perform the ritual on every pull request. The demons appear as a PR comment (updated on each push),
and the full ritual page is kept as a build artifact.

```yaml
name: Sanni Yakuma
on: pull_request
permissions:
  contents: read
  pull-requests: write
jobs:
  exorcise:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 200   # lets Gini Jala read the commit history
      - uses: dhananjaya-hbc/sanni-yakuma@main
        with:
          gemini-api-key: ${{ secrets.GEMINI_API_KEY }}
```

Add `GEMINI_API_KEY` as a repository secret. GitHub does not give secrets to pull requests from
forks, so the ritual runs only on branches of your own repository.

## Respect for the tradition

Sanni Yakuma is a living healing tradition. This project borrows the ritual's shape, not its sacred
purpose. The humour is aimed at the code sicknesses, as the ritual itself mocks the demons, and never
at the tradition, its performers or its beliefs. The masks are original drawings made in code for this
project, not copies of real masks.

## Credits

- About the ritual: [Sanni Yakuma on Wikipedia](https://en.wikipedia.org/wiki/Sanni_Yakuma), and the
  Science Museum Group's [Maha Kola Sanniya mask](https://collection.sciencemuseumgroup.org.uk/objects/co124339/polychrome-mask-representing-maha-kola-sanniya-chief-disease-demon)
  ("chief disease-demon … with 18 attendant demons").
- Model: [Gemma](https://ai.google.dev/gemma) by Google, via Google AI Studio.
- Libraries: [pydantic](https://github.com/pydantic/pydantic), [Jinja2](https://github.com/pallets/jinja),
  [lizard](https://github.com/terryyin/lizard), [google-genai](https://github.com/googleapis/python-genai),
  [httpx](https://github.com/encode/httpx), [rich](https://github.com/Textualize/rich),
  [python-dotenv](https://github.com/theskumar/python-dotenv), [json-repair](https://github.com/mangiucugna/json_repair).
- Font: [Noto Sans Sinhala](https://fonts.google.com/noto/specimen/Noto+Sans+Sinhala) (SIL Open Font License).
- Built for the DEV Hacktoberfest 2026 Open-Source AI Challenge ("Ghost in the Machine"), with help from
  Claude Code as an AI pair programmer.

## License

[MIT](LICENSE)
