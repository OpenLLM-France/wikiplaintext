# wikiplaintext

Get plain text from Wikipedia pages, as clean as possible.

Based on the latest versions of the [Wikimedia dumps](https://dumps.wikimedia.org/other/enterprise_html/runs),
the principle is to parse the HTML pages and get the cleanest version possible of a text,
with markdown format for headers, lists, and tables.

Examples of output can be found in the folder [tests/examples_markdown](tests/examples_markdown):
* Wikipedia pages : [with math](tests/examples_markdown/wikipedia_math.md), [with chemical formulas](tests/examples_markdown/wikipedia_chemistry.md), [with several kinds of tables](tests/examples_markdown/wikipedia_table.md)
* [Wikisource page](tests/examples_markdown/wikisource.md)
* [Wiktionary page](tests/examples_markdown/wiktionary_foreign_germanic.md)

This code was used to generate the HuggingFace datasets:
* [OpenLLM-France/wikipedia.fr](https://huggingface.co/datasets/OpenLLM-France/wikipedia.fr)
* [OpenLLM-France/wiktionary.fr](https://huggingface.co/datasets/OpenLLM-France/wiktionary.fr)
* [OpenLLM-France/wikisource.fr](https://huggingface.co/datasets/OpenLLM-France/wikisource.fr)

Those datasets are supposed to be cleaner and more complete than French subsets of [Wikimedia datasets](https://huggingface.co/datasets/wikimedia):
* [wikimedia/wikipedia (20231201.fr)](https://huggingface.co/datasets/wikimedia/wikipedia/viewer/20231101.fr) is missing the information behind the template. See [discussion here](https://huggingface.co/datasets/wikimedia/wikipedia/discussions/51).
* [wikimedia/wikisource (20231201.fr)](https://huggingface.co/datasets/wikimedia/wikisource/viewer/20231201.fr) is an incomplete dump (only contains 13 millions of words) and sometimes includes raw HTML code.

---

# Documentation

* [Installation](#installation)
* [Dump Wikipedia](#dump-wikipedia)
    * [Download the latest version available](#download-the-latest-version-available)
    * [Download a given version](#download-a-given-version)
    * [How to parallelize](#how-to-parallelize)
* [Dump Wiktionary](#dump-wiktionary)
    * [Download the latest version available](#download-the-latest-version-available-1)
    * [Download a given version](#download-a-given-version-1)
* [Dump Wikisource](#dump-wikisource)
* [Acknowledgements](#acknowledgements)

## Installation

```bash
git clone git@github.com:OpenLLM-France/wikiplaintext.git
cd wikiplaintext
pip install -r requirements.txt
```

All the scripts in the following are in the subfolder [`wikiplaintext`](wikiplaintext).

## Dump Wikipedia

### Download the latest version available

The following command will 
1. Download the latest version of Wikipedia dump from [Wikimedia Enterprise HTML dump](https://dumps.wikimedia.org/other/enterprise_html/runs)
2. Extract then ndjson files from the dump
3. Extract one HTML file per Wikipedia page
4. Parse each HTML file to get a clean plain text, and save it in a file

```bash
python dump_wiki_html.py \
    --output_dir /path/to/Wikipedia \
    --language fr \
    --source wiki
```

This will generate plain text files in subfolder
`/path/to/Wikipedia/{YYYYMMDD}/frwiki_txt/frwiki_namespace_0_*`
where `{YYYYMMDD}` is the latest version available.

One file per Wikipedia page, with the page id and title as a filename.

### Download a given version

```bash
python dump_wiki_html.py \
    --output_dir /path/to/Wikipedia \
    --language fr \
    --source wiki \
    --date 20231201
```

This will generate plain text files in subfolder
`/path/to/Wikipedia/20231201/frwiki_txt/frwiki_namespace_0_*`.

### How to parallelize

The process can be parallelized by launching several time the same command using option `--subset {i}/{n}`.
For example, 5 processes can be launched with the following commands:

```bash
python dump_wiki_html.py ... --subset 1/5 &
python dump_wiki_html.py ... --subset 2/5 &
python dump_wiki_html.py ... --subset 3/5 &
python dump_wiki_html.py ... --subset 4/5 &
python dump_wiki_html.py ... --subset 5/5 &
```

We recommend to run that in several windows of a `tmux` session (or `screen` session).

## Dump Wiktionary

### Download the latest version available

The process is very similar to Wikipedia (see above).

```bash
python dump_wiki_html.py \
    --output_dir /path/to/Wikipedia \
    --language fr \
    --source wiktionary
```

This will generate plain text files in subfolder
`/path/to/Wikipedia/{YYYYMMDD}/frwiktionary_txt/frwiktionary_namespace_0_*`
where `{YYYYMMDD}` is the latest version available.

One file per Wikipedia page, with the page id and title as a filename.

### Download a given version

```bash
python dump_wiki_html.py \
    --output_dir /path/to/Wikipedia \
    --language fr \
    --source wiktionary \
    --date 20231201
```

This will generate plain text files in subfolder
`/path/to/Wikipedia/20231201/frwiktionary_txt/frwiktionary_namespace_0_*`.

## Dump Wikisource

For Wikisource, it is a bit different because the Wikimedia dump is quite incomplete.

So the process consists in the following:
1. get all the page titles from the latest [HuggingFace dataset from Wikimedia](https://huggingface.co/datasets/wikimedia/wikisource)
2. download the HTML pages from the [Wikimedia API](https://www.mediawiki.org/wiki/API:Main_page)
3. parse the HTML pages and get the plain text

It can be run with the following command:

```bash
python dump_wikisource_api.py \
    --output_dir /path/to/Wikipedia \
    --language fr \
    --version 20231201 \
    --dump_html
```

This will generate plain text files in the folder
`/path/to/Wikipedia/20231201/frwikisource_txt/frwikisource_namespace_0_0`.

Also, with option `--dump_html` it will dump all HTML pages in the folder
`/path/to/Wikipedia/20231201/frwikisource_html/frwikisource_namespace_0_0`.
This is useful to restart the process later, if the cleaning code evolves, using:
```bash
python dump_wikisource_api2.py \
    --output_dir /path/to/Wikipedia \
    --language fr \
    --version 20231201
```

## Acknowledgements

* [Wikimedia](https://www.wikimedia.org/)
* [HuggingFace](https://huggingface.co/) for hosting the datasets