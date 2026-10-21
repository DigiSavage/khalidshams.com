"""Public engagement content, generated routes and rendering safety.

Run after building: python -m unittest tests/engagement/test_structure.py
"""
import copy
import json
import re
import sys
import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch
from urllib.parse import unquote, urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / 'dist'
sys.path.insert(0, str(ROOT))
import engagement_build  # noqa: E402

ROUTE = '/method/engagement/'


class Markup(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.ids, self.links, self.assets = [], [], []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.ids.append(attrs['id'])
        if tag == 'a' and attrs.get('href'):
            self.links.append(attrs['href'])
        if tag == 'script' and attrs.get('src'):
            self.assets.append(attrs['src'])
        if tag == 'link' and attrs.get('rel') == 'stylesheet':
            self.assets.append(attrs['href'])


def resolve(href):
    url = urlsplit(urljoin('https://khalidshams.com' + ROUTE, href))
    if url.scheme not in ('http', 'https') or url.netloc != 'khalidshams.com':
        return True
    target = DIST / unquote(url.path).lstrip('/')
    target = target / 'index.html' if url.path.endswith('/') else target
    if not target.is_file():
        return False
    return not url.fragment or unquote(url.fragment) in Markup(target.read_text()).ids


class Content(unittest.TestCase):
    def test_complete_journey_preserves_preparation_delivery_and_operating_ownership(self):
        data = engagement_build.load()
        self.assertEqual(tuple(stage['id'] for stage in data['stages']), engagement_build.STAGES)
        self.assertEqual(len(data['stages']), 11)
        for stage in data['stages']:
            with self.subTest(stage=stage['id']):
                for field in ('title', 'lead', 'owner', 'exit', 'hold'):
                    self.assertTrue(stage[field].strip())
                self.assertGreaterEqual(len(stage['actions']), 3)
                self.assertGreaterEqual(len(stage['artifact']['lines']), 3)
        self.assertEqual(set(data['audiences']), set(engagement_build.AUDIENCES))
        for audience in data['audiences'].values():
            self.assertTrue(all(audience.get(field) for field in ('label', 'opening', 'question', 'show', 'decision')))

    def test_invalid_content_fails_before_publishing(self):
        data = engagement_build.load()
        mutations = []
        broken = copy.deepcopy(data)
        broken['stages'].pop(0)
        mutations.append(broken)
        broken = copy.deepcopy(data)
        broken['audiences'].pop('risk')
        mutations.append(broken)
        broken = copy.deepcopy(data)
        broken['stages'][0]['owner'] = ''
        mutations.append(broken)
        for broken in mutations:
            with patch.object(engagement_build.json, 'loads', return_value=broken):
                with self.assertRaises(ValueError):
                    engagement_build.load()

    def test_render_escapes_content_in_markup_and_embedded_json(self):
        data = copy.deepcopy(engagement_build.load())
        attack = '</script><script>alert("untrusted")</script>'
        data['stages'][0]['lead'] = attack
        with patch.object(engagement_build, 'load', return_value=data):
            rendered = engagement_build.render('{{STAGES}}<script id="eg-data" type="application/json">{{ENGAGEMENT_DATA}}</script>', '', '')
        self.assertNotIn(attack, rendered)
        self.assertIn('&lt;/script&gt;', rendered)
        encoded = re.search(r'<script id="eg-data" type="application/json">(.*?)</script>', rendered, re.S).group(1)
        self.assertEqual(json.loads(encoded)['stages'][0]['lead'], attack)

    def test_public_files_use_site_punctuation(self):
        for path in ('content/engagement.json', 'templates/engagement.html',
                     'static/engagement/engine.js', 'static/engagement/engagement.js'):
            text = (ROOT / path).read_text()
            with self.subTest(path=path):
                self.assertIsNone(re.search(r'[\u2013\u2014]| -- ', text))


class Built(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = DIST / 'method/engagement/index.html'
        if not path.is_file():
            raise AssertionError('Build the site before running engagement structure checks')
        cls.html = path.read_text()
        cls.markup = Markup(cls.html)

    def test_generated_page_has_one_of_each_id_and_no_unresolved_tokens(self):
        self.assertNotIn('{{', self.html)
        duplicates = [key for key, count in Counter(self.markup.ids).items() if count > 1]
        self.assertEqual(duplicates, [])
        for stage in engagement_build.STAGES:
            self.assertIn('stage-' + stage, self.markup.ids)
        for element in ('eg-audience', 'eg-change', 'eg-copy', 'eg-download', 'eg-reset',
                        'eg-hours', 'eg-cost', 'eg-owner', 'eg-decision', 'eg-scope', 'eg-test', 'eg-operation'):
            self.assertIn(element, self.markup.ids)

    def test_all_internal_links_anchors_and_assets_exist(self):
        for href in sorted(set(self.markup.links + self.markup.assets)):
            with self.subTest(href=href):
                self.assertTrue(resolve(href), href)

    def test_home_method_and_navigation_expose_the_new_workflow(self):
        for path in ('index.html', 'method/index.html'):
            html = (DIST / path).read_text()
            self.assertGreaterEqual(html.count('href="' + ROUTE + '"'), 3, path)
        self.assertIn(f'https://khalidshams.com{ROUTE}', (DIST / 'sitemap.xml').read_text())
        entries = json.loads((DIST / 'search.json').read_text())
        relevant = [entry for entry in entries if entry['u'].split('#')[0] == ROUTE]
        self.assertGreaterEqual(len(relevant), 6)
        for entry in relevant:
            self.assertTrue(resolve(entry['u']), entry['u'])

    def test_rendered_data_is_complete_and_disclosures_remain_available_without_scripts(self):
        encoded = re.search(r'<script id="eg-data" type="application/json">(.*?)</script>', self.html, re.S).group(1)
        self.assertEqual(json.loads(encoded), engagement_build.load())
        self.assertIn('<noscript>', self.html)
        self.assertIn('not a historical client engagement', self.html)
        self.assertIn('Not measured.', self.html)
        self.assertIn('funding is conditional', self.html)
        self.assertEqual(self.html.count('class="eg-artifact"'), 11)


if __name__ == '__main__':
    unittest.main()
