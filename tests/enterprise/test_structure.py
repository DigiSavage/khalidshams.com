import copy
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

import enterprise_build as studio


class StudioStructure(unittest.TestCase):
    def test_registry_and_svg_are_complete(self):
        data = studio.load()
        self.assertEqual(len(data['examples']), 2)
        svg = ET.fromstring(studio.scene())
        self.assertEqual({e.attrib['data-node'] for e in svg.iter() if 'data-node' in e.attrib},
                         {'identity','evidence','model','proposal','gate','review','execute','receipt','budget'})
        ids = [e.attrib['id'] for e in svg.iter() if 'id' in e.attrib]
        self.assertEqual(len(ids), len(set(ids)))

    def test_incomplete_examples_fail_the_build(self):
        data = studio.load()
        for field in studio.EXAMPLE_FIELDS - {'id'}:
            broken = copy.deepcopy(data)
            del broken['examples'][0][field]
            with self.assertRaises(ValueError):
                studio.validate(broken)

    def test_both_examples_are_readable_without_javascript(self):
        html = studio.render((studio.ROOT/'templates/enterprise.html').read_text(), '', '')
        self.assertIn('example-documents', html)
        self.assertIn('example-assistant', html)
        for item in studio.load()['examples']:
            self.assertIn(item['goal'].replace("'", '&#x27;'), html)
        self.assertNotIn('{{GOAL}}', html)
        self.assertIn('source-privacy', html)

    def test_site_route_search_and_navigation_are_wired(self):
        dist = studio.ROOT/'dist'
        self.assertTrue((dist/'architect/agent-studio/index.html').is_file())
        for path in ['sitemap.xml','search.json','index.html','architect/index.html','method/index.html']:
            self.assertIn(studio.ROUTE, (dist/path).read_text())
        self.assertEqual((studio.ROOT/'templates/masthead.html').read_text().count(studio.ROUTE), 2)


if __name__ == '__main__':
    unittest.main()
