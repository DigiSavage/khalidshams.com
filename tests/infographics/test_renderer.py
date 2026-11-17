"""Infographic contracts: no silent omission, cropping, stale asset or broken post mapping."""
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
loader = importlib.util.spec_from_file_location('linkedin_infographics', ROOT/'tools/linkedin_infographics.py')
renderer = importlib.util.module_from_spec(loader)
loader.loader.exec_module(renderer)


class InfographicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.specs = renderer.load_specs()
        cls.manifest = json.loads(renderer.MANIFEST_PATH.read_text())
        cls.rendered = {s['slug']: renderer.render(s) for s in cls.specs}

    def test_every_prepared_post_has_one_exact_asset(self):
        expected = {str(p.relative_to(ROOT)) for p in (ROOT/'content/posts').glob('*.md')
                    if re.search(r'^visual_required:\s*true\s*$',
                                 p.read_text().split('---', 2)[1], re.MULTILINE)}
        actual = [s['post'] for s in self.specs if s.get('post')]
        self.assertEqual(set(actual), expected)
        self.assertEqual(len(actual), len(set(actual)))

    def test_manifest_assets_are_complete_readable_and_current(self):
        self.assertEqual((self.manifest['width'], self.manifest['height']), (1200, 1500))
        self.assertEqual(len(self.manifest['items']), len(self.specs))
        specs = {s['slug']: s for s in self.specs}
        for item in self.manifest['items']:
            with self.subTest(slug=item['slug']):
                data, boxes = self.rendered[item['slug']]
                self.assertEqual(item['asset'], f"content/images/{item['slug']}.png")
                self.assertEqual((ROOT/item['asset']).read_bytes(), data)
                self.assertEqual(item['sha256'], hashlib.sha256(data).hexdigest())
                self.assertEqual(item['alt'], specs[item['slug']]['alt'])
                self.assertEqual(item['post'], specs[item['slug']].get('post'))
                self.assertGreater(len(item['alt']), 80)
                self.assertLessEqual(len(item['alt']), 1000)
                with Image.open(io.BytesIO(data)) as image:
                    self.assertEqual(image.size, (1200, 1500))
                    self.assertEqual(image.mode, 'RGB')
                self.assertGreater(len(boxes), 10)

    def test_graphics_offer_multiple_mechanisms(self):
        self.assertEqual({s['layout'] for s in self.specs}, renderer.LAYOUTS)
        for spec in self.specs:
            self.assertTrue(spec['test'].strip())
            self.assertTrue(spec['boundary'].strip())

    def test_standalone_demo_is_synthetic_and_not_a_scheduled_post(self):
        spec = next(s for s in self.specs if s['slug']=='a-yes-has-a-boundary-recording')
        self.assertIsNone(spec['post'])
        self.assertIn('PAYLOAD_CHANGED', spec['test'])
        self.assertIn('synthetic writes: 0', spec['test'])
        self.assertIn('No payment', spec['boundary'])

    def test_overflow_is_rejected_instead_of_shrinking_or_cropping(self):
        spec = copy.deepcopy(self.specs[0])
        spec['title'] = 'This is a very long title that cannot possibly fit. ' * 10
        with self.assertRaises(renderer.LayoutError): renderer.render(spec)
        canvas = renderer.Canvas()
        with self.assertRaises(renderer.LayoutError): canvas.text('W'*80, (0,0,50,50), size=30)
        with self.assertRaises(renderer.LayoutError): canvas.text('test', (1190,0,40,50))
        with self.assertRaises(renderer.LayoutError): canvas.rect((0,1490,100,40))

    def test_invalid_mappings_and_unreadable_alt_are_rejected(self):
        changes = [dict(slug='../escape'), dict(post='content/posts/../private.md'),
                   dict(post='content/posts/2026-11-18-other-slug.md'), dict(layout='unknown'),
                   dict(alt='x'*1001), dict(title='An unsupported — dash')]
        for change in changes:
            spec = dict(self.specs[0], **change)
            with self.subTest(change=list(change)), self.assertRaises(ValueError):
                renderer.validate_spec(spec)

    def test_invalid_shape_cannot_silently_omit_content(self):
        spec = copy.deepcopy(next(s for s in self.specs if s['layout']=='matrix'))
        spec['columns'].append('UNRENDERED')
        with self.assertRaises(ValueError): renderer.render(spec)
        spec = copy.deepcopy(next(s for s in self.specs if s['layout']=='fork'))
        spec['branches'].append(dict(title='UNRENDERED', detail='must be rejected'))
        with self.assertRaises(ValueError): renderer.render(spec)

    def test_batch_preflight_does_not_write_before_later_layout_failure(self):
        good, bad = copy.deepcopy(self.specs[:2])
        bad['title'] = 'Will not fit ' * 100
        with patch.object(renderer, 'load_specs', return_value=[good,bad]), patch.object(Path,'write_bytes') as write:
            with self.assertRaises(renderer.LayoutError): renderer.build()
            write.assert_not_called()


if __name__ == '__main__': unittest.main()
