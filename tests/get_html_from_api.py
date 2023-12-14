# Source: https://www.mediawiki.org/wiki/API:Parsing_wikitext#Python

import argparse
import urllib.parse

parser = argparse.ArgumentParser(description="Get HTML from a page, given the title")
parser.add_argument("page", help="Page to get", default="Feux de forêt de 2023 en Nouvelle-Écosse", nargs="?")
parser.add_argument("--language", default="fr", help="language")
parser.add_argument("--domain", default="wikipedia", help="wikipedia / wikisource / ...")
parser.add_argument("--output", default=None, help="Output file (will print on stdout if not specified)")
args = parser.parse_args()

import requests

session = requests.Session()

base_url = f"https://{args.language}.{args.domain}.org"
api_url = f"{base_url}/w/api.php"

args.page = urllib.parse.unquote(args.page.replace(" ", "_"))

params = {
    "action": "parse",
    "page": args.page,
    "format": "json"
}

response = session.get(url=api_url, params=params)
data = response.json()

if "error" in data:
    raise RuntimeError(f"Failed to get {base_url}/wiki/{args.page}\nError: {data['error'].get('info', data['error'])}")

print(data["parse"]["text"]["*"], file = open(args.output, "w") if args.output else None)