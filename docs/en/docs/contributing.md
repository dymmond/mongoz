# Contributing

Thank you for showing interes in contributing to Mongoz. There are many ways you can help and contribute to the
project.

* Try Mongoz and [report bugs and issues](https://github.com/dymmond/mongoz/issues/new) you find.
* [Implement new features](https://github.com/dymmond/mongoz/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22).
* Help othes by [reviewing pull requests](https://github.com/dymmond/mongoz/pulls).
* Help writting documentation.
* Use the discussions and actively participate on them.
* Become an contributor by helping Mongoz growing and spread the words across small, medium, large or any company
size.

## Reporting possible bugs and issues

It is natural that you might find something that Mongoz should support or even experience some sorte of unexpected
behaviour that needs addressing.

The way we love doing things is very simple, contributions should start out with a
[discussion](https://github.com/dymmond/mongoz/discussions). The potential bugs shall be raised as "Potential Issue"
in the discussions, the feature requests may be raised as "Ideas".

We can then decide if the discussion needs to be escalated into an "Issue" or not.

When reporting something you should always try to:

* Be as more descriptive as possible
* Provide as much evidence as you can, something like:
    * OS platform
    * Python version
    * Installed dependencies
    * Code snippets
    * Tracebacks

Avoid putting examples extremely complex to understand and read. Simplify the examples as much as possible to make
it clear to understand and get the required help.

Suspected vulnerabilities must not be reported in a public issue or discussion. Use the repository
Security tab's private **Report a vulnerability** workflow described in `SECURITY.md`.

## Development

To develop for Mongoz, create a fork of the [Mongoz repository](https://github.com/dymmond/mongoz) on GitHub.

After, clone your fork with the follow command replacing `YOUR-USERNAME` wih your GitHub username:

```shell
$ git clone https://github.com/YOUR-USERNAME/mongoz
```

Mongoz uses [Hatch](https://hatch.pypa.io/latest/) as the command owner for development and
validation. Install the same Hatch version used by CI:

```shell
pip install hatch==1.16.5
```

Hatch creates each environment on first use. The testing, documentation, quality, and packaging
dependencies are pinned in `pyproject.toml`, so local gates and CI resolve the same tools. Mongoz
does not use a lockfile: the isolated wheel proof deliberately resolves the published runtime
dependency bounds and then runs `pip check`. It also reinstalls PyMongo 4.13.0 and repeats the
installed-wheel MongoDB smoke so the declared driver floor remains executable.

### MongoDB test services

The standalone and replica-set services use an immutable MongoDB 8.0.29 image. Their credentials
are test-only, both ports bind only to localhost, and the project names keep their data isolated.

Start, probe, and stop standalone MongoDB:

```shell
hatch run mongodb-standalone-up
hatch run mongodb-standalone-smoke
hatch run mongodb-standalone-down
```

Start, prove transaction commit and rollback, and stop the replica set:

```shell
hatch run mongodb-replica-set-up
hatch run mongodb-replica-set-smoke
hatch run mongodb-replica-set-down
```

The `down` commands remove their project-owned volumes. Do not store development data in these
test services.

### Tests and coverage

Tests require standalone MongoDB. Run the full suite or pass a focused pytest target:

```shell
hatch run test:test -q
hatch run test:focused tests/registry/test_lifecycle.py -q
```

Run the supported standard CPython matrix (3.10 through 3.14; no free-threaded build):

```shell
hatch run matrix:test -q
```

Run corrected Mongoz source and branch coverage:

```shell
hatch run test:coverage -q
```

Coverage writes `coverage.xml` and `coverage.json` and fails below the 88.95% regression floor.
The coverage command also enforces the warning ratchet. To run that policy without coverage:

```shell
hatch run test:warnings -q
```

The warning ratchet rejects unknown warning categories and growth in the remaining known category.
Pydantic deprecations are not allowlisted, so introducing a deprecated Pydantic construction fails
the gate instead of being hidden by a warning filter or dependency pin.

### Static quality

All CI checks are read-only:

```shell
hatch run lint
hatch run format-check
hatch run typing
```

Ruff owns linting, import ordering, and formatting. Apply intentional formatting changes with:

```shell
hatch run format
```

Ty is the canonical type checker. The gate checks the complete `mongoz` package plus positive
consumer contracts, while `hatch run typing-negative` verifies that intentional negative
fixtures fail for their exact expected rules. Do not add blanket exclusions or suppression
comments to make the gate pass; repair the owning annotation or implementation instead.

### Performance and security evidence

CodSpeed benchmarks are fixed-workload Python 3.13 regression checks. Each benchmark uses 20 warmup
rounds and 100 measured rounds:

```shell
hatch run matrix.py3.13:focused benchmarks --codspeed
```

Database latency is intentionally separate. With standalone MongoDB running, the informational
driver/ODM benchmark uses a 1,000-document dataset, five warmups, and nine repeats:

```shell
hatch run matrix.py3.13:python benchmarks/database.py
```

Do not turn a noisy end-to-end result into a framework performance claim. Establish the Python-side
owner first and retain raw PyMongo as the driver/network control.

Run the project dependency vulnerability audit with:

```shell
hatch run security:audit
```

CodeQL and dependency review run in hosted CI. The audit covers known published advisories; it is
not a malicious-package detector or a substitute for review.

### Enable pre-commit

Pre-commit uses the same read-only Ruff checks as CI. Enable it inside the clone:

```shell
hatch run pre-commit install
```

Run every hook explicitly with:

```shell
hatch run pre-commit-check
```

### Documentation and package proof

Validate includes, internal links and anchors, Python example contracts, and strict English and
Portuguese builds:

```shell
hatch run docs:validate
```

With standalone MongoDB running, build and check wheel/sdist, install the wheel into a clean
environment, verify its metadata and dependencies, and run its real-MongoDB smoke:

```shell
hatch run package:validate
```

### Full local acceptance

The full command starts both isolated MongoDB topologies as needed and always tears them down:

```shell
hatch run acceptance
```

## Documentation

Improving the documentation is quite easy and it is placed inside the `mongoz/docs` folder.

To build all the documentation:

```shell
$ hatch run docs:build
```

### Docs live (serving the docs)

During local development, there is a script that builds the site and checks for any changes, live-reloading:

```shell
$ hatch run docs:serve
```

It will serve the documentation on `http://localhost:8000`.

If you wish to serve on a different port:

```shell
$ hatch run docs:serve -p <PORT-NUMBER>
```

That way, you can edit the documentation/source files and see the changes live.

!!! tip
    Alternatively, you can perform the same steps that scripts does manually.

    Go into the language directory, for the main docs in English it's at `docs/en/`:

    ```console
    $ cd docs/en/
    ```

    Then run `mkdocs` in that directory:

    ```console
    $ mkdocs serve --dev-addr 8000
    ```

### Docs Structure

The documentation uses <a href="https://www.mkdocs.org/" class="external-link" target="_blank">MkDocs</a>.

And there are extra tools/scripts in place to handle translations in `./scripts/docs.py`.

!!! tip
    You don't need to see the code in `./scripts/docs.py`, you just use it in the command line.

All the documentation is in Markdown format in the directory `./docs/en/`.

Many of the tutorials have blocks of code.

In most of the cases, these blocks of code are actual complete applications that can be run as is.

In fact, those blocks of code are not written inside the Markdown, they are Python files in the `./docs_src/` directory.

And those Python files are included/injected in the documentation when generating the site.

### Translations

Help with translations is VERY MUCH appreciated! And it can't be done without the help from the community.

Here are the steps to help with translations.

#### Tips and guidelines

* Check the currently <a href="https://github.com/dymmond/mongoz/pulls" class="external-link" target="_blank">existing pull requests</a> for your language. You can filter the pull requests by the ones with the label for your language. For example, for Spanish, the label is <a href="https://github.com/dymmond/mongoz/pulls?q=is%3Aopen+sort%3Aupdated-desc+label%3Alang-es+label%3Aawaiting-review" class="external-link" target="_blank">`lang-es`</a>.

* Review those pull requests, requesting changes or approving them. For the languages I don't speak, I'll wait for several others to review the translation before merging.

!!! tip
    You can <a href="https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/commenting-on-a-pull-request" class="external-link" target="_blank">add comments with change suggestions</a> to existing pull requests.

    Check the docs about <a href="https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/about-pull-request-reviews" class="external-link" target="_blank">adding a pull request review</a> to approve it or request changes.

* Check if there's a <a href="https://github.com/dymmond/mongoz/discussions/categories/translations" class="external-link" target="_blank">GitHub Discussion</a> to coordinate translations for your language. You can subscribe to it, and when there's a new pull request to review, an automatic comment will be added to the discussion.

* If you translate pages, add a single pull request per page translated. That will make it much easier for others to review it.

* To check the 2-letter code for the language you want to translate, you can use the table <a href="https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes" class="external-link" target="_blank">List of ISO 639-1 codes</a>.

#### Existing language

Let's say you want to translate a page for a language that already has translations for some pages, like Spanish.

In the case of Spanish, the 2-letter code is `es`. So, the directory for Spanish translations is located at `docs/es/`.

!!! tip
    The main ("official") language is English, located at `docs/en/`.

Now run the live server for the docs in Spanish:

```shell
// Use the command "live" and pass the language code as a CLI argument
$ hatch run docs:serve_lang es
```

!!! tip
    Alternatively, you can perform the same steps that scripts does manually.

    Go into the language directory, for the Spanish translations it's at `docs/es/`:

    ```console
    $ cd docs/es/
    ```

    Then run `mkdocs` in that directory:

    ```console
    $ mkdocs serve --dev-addr 8000
    ```

Now you can go to <a href="http://127.0.0.1:8000" class="external-link" target="_blank">http://127.0.0.1:8000</a> and see your changes live.

You will see that every language has all the pages. But some pages are not translated and have an info box at the top, about the missing translation.

Now let's say that you want to add a translation for the section [Fields](fields.md){.internal-link target=_blank}.

* Copy the file at:

```
docs/en/docs/fields.md
```

* Paste it in exactly the same location but for the language you want to translate, e.g.:

```
docs/es/docs/fields.md
```

!!! tip
    Notice that the only change in the path and file name is the language code, from `en` to `es`.

If you go to your browser you will see that now the docs show your new section (the info box at the top is gone). 🎉

Now you can translate it all and see how it looks as you save the file.

#### New Language

Let's say that you want to add translations for a language that is not yet translated, not even some pages.

Let's say you want to add translations for Creole, and it's not yet there in the docs.

Checking the link from above, the code for "Creole" is `ht`.

The next step is to run the script to generate a new translation directory:

```shell
// Use the command new-lang, pass the language code as a CLI argument
$ hatch run docs:new_lang ht

Successfully initialized: docs/ht
```

Now you can check in your code editor the newly created directory `docs/ht/`.

That command created a file `docs/ht/mkdocs.yml` with a simple config that inherits everything from the `en` version:

```yaml
INHERIT: ../en/mkdocs.yml
site_dir: '../../site_lang/ht'
```

!!! tip
    You could also simply create that file with those contents manually.

That command also created a dummy file `docs/ht/index.md` for the main page, you can start by translating that one.

You can continue with the previous instructions for an "Existing Language" for that process.

You can make the first pull request with those two files, `docs/ht/mkdocs.yml` and `docs/ht/index.md`. 🎉

#### Preview the result

As already mentioned above, you can use the `./scripts/docs.py` with the `live` command to preview the results (or `mkdocs serve`).

Once you are done, you can also test it all as it would look online, including all the other languages.

To do that, first build all the docs:


```shell
// Use the command "build-all", this will take a bit
$ hatch run docs:build
```

You can also collect documentation for one language

```shell
// Use the command "build-lang", this will take a bit
$ hatch run docs:build_lang your_lang
```

This builds all those independent MkDocs sites for each language, combines them, and generates the final output at `./site_lang/`.

Then you can serve that with the command `serve`:

```shell
// Use the command "dev" after running "build-all" or "build-lang -l your_lang"
$ hatch run docs:dev

Warning: this is a very simple server. For development, use mkdocs serve instead.
This is here only to preview a site with translations already built.
Make sure you run the build-all command first.
Serving at: http://127.0.0.1:8000
```

## Building Mongoz

To build a package locally, run:

```shell
$ hatch build
```

Alternatively running:

```
$ hatch shell
```

It will install the requirements and create a local build in your virtual environment.

## Releasing

*This section is for the maintainers of `Mongoz`*.

### Building the Mongoz for release

Before releasing a new package into production some considerations need to be taken into account.

* **Changelog**
    * Like many projects, we follow the format from [keepchangelog](https://keepachangelog.com/en/1.0.0/).
    * [Compare](https://github.com/dymmond/mongoz/compare/) `main` with the release tag and list of the entries
that are of interest to the users of the framework.
        * What **must** go in the changelog? added, changed, removed or deprecated features and the bug fixes.
        * What is **should not go** in the changelog? Documentation changes, tests or anything not specified in the
point above.
        * Make sure the order of the entries are sorted by importance.
        * Keep it simple.

* *Version bump*
    * The version should be in `__init__.py` of the main package.

#### Releasing

Once the `release` PR is merged, create a new [release](https://github.com/dymmond/mongoz/releases/new)
that includes:

Example:

There will be a release of the version `0.2.3`, this is what it should include.

* Release title: `Version 0.2.3`.
* Tag: `0.2.3`.
* The description should be copied from the changelog.

Once the release is created, it should automatically upload the new version to PyPI. If something
does not work with PyPI the release can be done by running `scripts/release`.
