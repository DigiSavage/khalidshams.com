"""Infographic contracts: no silent omission, cropping, stale asset, broken post mapping,
redrawn published graphic or card that is all fine print."""
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
loader = importlib.util.spec_from_file_location('linkedin_infographics', ROOT/'tools/linkedin_infographics.py')
renderer = importlib.util.module_from_spec(loader)
loader.loader.exec_module(renderer)
STAGES = ('scope', 'harden', 'anchor', 'measure', 'sustain')


class InfographicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.specs = renderer.load_specs()
        cls.manifest = json.loads(renderer.MANIFEST_PATH.read_text())
        # A published graphic is a record: it is verified by hash and never drawn again.
        cls.live = [s for s in cls.specs if not renderer.is_frozen(s)]
        cls.frozen = [s for s in cls.specs if renderer.is_frozen(s)]
        cls.rendered = {s['slug']: renderer.render(s) for s in cls.live}

    def live_of(self, layout):
        return copy.deepcopy(next(s for s in self.live if s['layout'] == layout))

    def test_every_prepared_post_has_one_exact_asset(self):
        expected = {str(p.relative_to(ROOT)) for p in (ROOT/'content/posts').glob('*.md')
                    if re.search(r'^visual_required:\s*true\s*$',
                                 p.read_text().split('---', 2)[1], re.MULTILINE)}
        actual = [s['post'] for s in self.specs if s.get('post')]
        self.assertEqual(set(actual), expected)
        self.assertEqual(len(actual), len(set(actual)))

    def test_manifest_assets_are_complete_readable_and_current(self):
        renderer.verify_manifest(self.manifest, self.specs)
        self.assertEqual((self.manifest['schema_version'], self.manifest['width'], self.manifest['height']), (1, 1200, 1500))
        self.assertEqual(len(self.manifest['items']), len(self.specs))
        specs = {s['slug']: s for s in self.specs}
        current = renderer.input_fingerprints()['renderer']['sha256']
        for item in self.manifest['items']:
            with self.subTest(slug=item['slug']):
                spec = specs[item['slug']]
                data = (ROOT/item['asset']).read_bytes()
                self.assertEqual(item['asset'], f"content/images/{item['slug']}.png")
                self.assertEqual(item['sha256'], hashlib.sha256(data).hexdigest())
                self.assertEqual(item['spec_sha256'], renderer.spec_fingerprint(spec))
                self.assertEqual(item['alt'], spec['alt'])
                self.assertEqual(item['post'], spec.get('post'))
                self.assertGreater(len(item['alt']), 80)
                self.assertLessEqual(len(item['alt']), 1000)
                with Image.open(io.BytesIO(data)) as image:
                    self.assertEqual(image.size, (1200, 1500))
                    self.assertEqual(image.mode, 'RGB')
                if item['slug'] in self.rendered:
                    self.assertEqual(item['renderer_sha256'], current)
                    self.assertGreater(len(self.rendered[item['slug']][1]), 30)

    def test_render_output_meets_the_publisher_image_contract(self):
        data, _ = self.rendered[self.live[0]['slug']]
        with Image.open(io.BytesIO(data)) as image:
            self.assertEqual((image.format, image.size, image.mode), ('PNG', (1200, 1500), 'RGB'))

    def test_changed_renderer_source_is_rejected(self):
        original = Path.read_bytes
        source = Path(renderer.__file__).resolve()
        def changed(path):
            data = original(path)
            return data+b'\n# changed renderer source\n' if path == source else data
        with patch.object(Path, 'read_bytes', changed), self.assertRaisesRegex(ValueError, 'Renderer source'):
            renderer.verify_manifest(self.manifest, self.specs)

    def test_changed_font_is_rejected(self):
        original = Path.read_bytes
        font = renderer.FONTS/renderer.FONT_FILES['sans']
        def changed(path):
            data = original(path)
            return data+b'changed' if path == font else data
        with patch.object(Path, 'read_bytes', changed), self.assertRaisesRegex(ValueError, 'font inputs'):
            renderer.verify_manifest(self.manifest, self.specs)

    def test_changed_spec_is_rejected_even_when_it_still_fits(self):
        specs = copy.deepcopy(self.specs)
        target = next(s for s in specs if s['slug'] == self.live[0]['slug'])
        target['subtitle'] = 'Changed meaning that still fits.'
        with self.assertRaisesRegex(ValueError, 'Specification'):
            renderer.verify_manifest(self.manifest, specs)

    def test_tampered_committed_asset_is_rejected(self):
        original = Path.read_bytes
        for item in (self.manifest['items'][0], self.manifest['items'][-1]):
            asset = ROOT/item['asset']
            def changed(path, asset=asset):
                data = original(path)
                return data+b'changed' if path == asset else data
            with self.subTest(asset=item['asset']), patch.object(Path, 'read_bytes', changed), \
                    self.assertRaisesRegex(ValueError, 'Asset hash mismatch'):
                renderer.verify_manifest(self.manifest, self.specs)

    def test_check_renders_bounds_but_ignores_platform_raster_bytes(self):
        def different_raster(spec):
            data, boxes = self.rendered[spec['slug']]
            return data+b'different platform raster bytes', boxes
        with patch.object(renderer, 'render', side_effect=different_raster), patch('builtins.print'):
            self.assertEqual(renderer.build(check=True), self.manifest)

    def test_check_rejects_overflow_even_with_committed_assets(self):
        specs = copy.deepcopy(self.specs)
        next(s for s in specs if s['slug'] == self.live[0]['slug'])['title'] = 'Cannot fit the title region\n' + 'at all ' * 60
        with patch.object(renderer, 'load_specs', return_value=specs), self.assertRaises(renderer.LayoutError):
            renderer.build(check=True)

    # ---- published graphics are records ----------------------------------------------

    def test_the_published_logging_graphic_is_frozen_with_its_original_renderer(self):
        slugs = [s['slug'] for s in self.frozen]
        self.assertIn('the-cost-of-seeing-everything', slugs)
        entry = next(e for e in self.manifest['items'] if e['slug'] == 'the-cost-of-seeing-everything')
        self.assertNotEqual(entry['renderer_sha256'], renderer.input_fingerprints()['renderer']['sha256'])
        self.assertEqual(entry['sha256'], hashlib.sha256((ROOT/entry['asset']).read_bytes()).hexdigest())

    def test_build_never_rewrites_or_redraws_a_published_graphic(self):
        frozen_assets = {ROOT/'content/images'/f"{s['slug']}.png" for s in self.frozen}
        written = []
        def fake_render(spec):
            self.assertFalse(renderer.is_frozen(spec), 'a published graphic was drawn again')
            return self.rendered[spec['slug']]
        with patch.object(renderer, 'render', side_effect=fake_render), patch('builtins.print'), \
                patch.object(Path, 'write_bytes', lambda path, data: written.append(path)), \
                patch.object(Path, 'write_text', lambda path, text, **kw: written.append(path)):
            manifest = renderer.build()
        self.assertTrue(written)
        self.assertFalse(frozen_assets & set(written))
        carried = {e['slug']: e for e in manifest['items']}
        for spec in self.frozen:
            self.assertEqual(carried[spec['slug']], next(e for e in self.manifest['items'] if e['slug'] == spec['slug']))
        with patch('builtins.print'), self.assertRaisesRegex(ValueError, 'published'):
            renderer.build(only=self.frozen[0]['slug'])

    def test_changed_published_specification_is_rejected(self):
        specs = copy.deepcopy(self.specs)
        next(s for s in specs if s['slug'] == self.frozen[0]['slug'])['alt'] += ' Edited after publication.'
        with self.assertRaisesRegex(ValueError, 'Published graphic'):
            renderer.verify_manifest(self.manifest, specs)

    def test_a_post_that_publishes_later_still_verifies_without_a_manifest_change(self):
        # The publisher flips status on main between renders. That must never block the next run.
        soon = self.live[0]['slug']
        real = renderer.post_status
        with patch.object(renderer, 'post_status', lambda spec: 'published' if spec['slug'] == soon else real(spec)), \
                patch('builtins.print'):
            renderer.verify_manifest(self.manifest, self.specs)
            self.assertEqual(renderer.build(check=True), self.manifest)

    # ---- the design contract ---------------------------------------------------------

    def test_graphics_offer_multiple_mechanisms(self):
        self.assertEqual({s['layout'] for s in self.live}, renderer.LAYOUTS)
        self.assertEqual(set(renderer.RENDERERS), renderer.LAYOUTS)
        for spec in self.live:
            self.assertTrue(spec['test'].strip())
            self.assertTrue(spec['boundary'].strip())

    def test_whole_process_and_authored_handoff_are_visible(self):
        for spec in self.live:
            with self.subTest(slug=spec['slug']):
                process = spec['process']
                self.assertIn(process['focus'], STAGES)
                _, boxes = self.rendered[spec['slug']]
                texts = [box['text'] for box in boxes]
                visible = '\n'.join(texts)
                for stage in STAGES:
                    self.assertIn(stage.title(), texts)
                    self.assertIn(renderer.STAGE_REMIT[stage], texts)
                for label in ('BRING IN', 'LEAVE WITH', 'CHECK IT', 'LIMIT', process['bring_in'],
                              process['leave_with'], spec['test'], spec['boundary']):
                    self.assertIn(label, texts)
                self.assertEqual(sum('IN FOCUS' in t for t in texts), 1)
                self.assertIn(f"{process['focus'].upper()} · IN FOCUS", visible)
                self.assertIn(process['focus'], spec['alt'].lower())

    def test_every_card_keeps_a_phone_layer_and_a_type_floor(self):
        for spec in self.live:
            with self.subTest(slug=spec['slug']):
                _, boxes = self.rendered[spec['slug']]
                self.assertGreaterEqual(min(b['font_size'] for b in boxes), renderer.MIN_TEXT)
                total = sum(len(b['text']) for b in boxes)
                big = sum(len(b['text']) for b in boxes if b['font_size'] >= renderer.READABLE)
                self.assertGreaterEqual(big, renderer.PHONE_SHARE*total)
                for box in boxes:
                    x, y, w, h = box['box']
                    self.assertTrue(x >= -1 and y >= -1 and x+w <= 1201 and y+h <= 1501, box)
        canvas = renderer.Canvas()
        with self.assertRaisesRegex(renderer.LayoutError, 'floor'): canvas.label('too small', (100, 100), 14)
        with self.assertRaisesRegex(renderer.LayoutError, 'floor'): canvas.text('too small', (0, 0, 400, 60), size=12)

    def test_a_card_of_fine_print_is_rejected(self):
        spec = self.live_of('ledger')
        with patch.object(renderer, 'PHONE_SHARE', 0.95), self.assertRaisesRegex(renderer.LayoutError, 'fine print'):
            renderer.render(spec)

    def test_every_symbol_draws_and_unknown_symbols_are_rejected(self):
        canvas = renderer.Canvas()
        for i, name in enumerate(sorted(renderer.ICONS)):
            canvas.icon(name, 60 + (i % 10)*100, 60 + (i//10)*100, 48)
        self.assertGreaterEqual(len(renderer.ICONS), 30)
        with self.assertRaisesRegex(ValueError, 'Unknown icon'): canvas.icon('sparkles', 50, 50, 40)
        spec = self.live_of('route'); spec['steps'][0]['icon'] = 'sparkles'
        with self.assertRaisesRegex(ValueError, 'Unknown icon'): renderer.render(spec)

    def test_cost_gold_is_reserved_for_cost_subjects(self):
        for spec in self.live:
            tones = [spec.get('tone'), spec.get('rule_tone')] + [b.get('tone') for b in spec.get('branches', [])]
            if 'cost' in tones:
                words = (spec['category'] + ' ' + spec['subtitle'] + ' ' + spec['alt']).lower()
                self.assertRegex(words, r'cost|econom|price|invoice', spec['slug'])

    def test_invalid_or_missing_process_cannot_publish_a_contextless_card(self):
        base = self.live[0]
        missing = copy.deepcopy(base)
        missing.pop('process', None)
        with self.assertRaises(ValueError): renderer.render(missing)
        valid = copy.deepcopy(base['process'])
        for process in (None, [], {}, dict(valid, focus='unknown'),
                        dict(valid, focus=''), dict(valid, bring_in=''),
                        dict(valid, leave_with=' '), dict(valid, leave_with=12)):
            spec = dict(base, process=process)
            with self.subTest(process=process), self.assertRaises(ValueError):
                renderer.render(spec)

    def test_standalone_visuals_are_not_scheduled_posts(self):
        spec = next(s for s in self.specs if s['slug'] == 'a-yes-has-a-boundary-recording')
        self.assertIsNone(spec['post'])
        self.assertIn('PAYLOAD_CHANGED', spec['test'])
        self.assertIn('synthetic writes: 0', spec['test'])
        self.assertIn('No payment', spec['boundary'])
        self.assertIn('SYNTHETIC', spec['example_label'])
        exemplar = next(s for s in self.specs if s['slug'] == 'budget-the-logs-keep-the-evidence')
        self.assertIsNone(exemplar['post'])
        self.assertIn('not permission to delete', exemplar['boundary'])

    def test_overflow_is_rejected_instead_of_shrinking_or_cropping(self):
        spec = copy.deepcopy(self.live[0])
        spec['title'] = 'A first line\n' + 'that cannot possibly fit. ' * 10
        with self.assertRaises(renderer.LayoutError): renderer.render(spec)
        spec = copy.deepcopy(self.live[0]); spec['title'] = 'One line only'
        with self.assertRaisesRegex(renderer.LayoutError, 'two lines'): renderer.render(spec)
        spec = copy.deepcopy(self.live[0]); spec['subtitle'] = 'A subtitle that runs on and on. ' * 6
        with self.assertRaises(renderer.LayoutError): renderer.render(spec)
        canvas = renderer.Canvas()
        with self.assertRaises(renderer.LayoutError): canvas.text('W'*80, (0, 0, 50, 50), size=30)
        with self.assertRaises(renderer.LayoutError): canvas.text('test', (1190, 0, 40, 50))
        with self.assertRaises(renderer.LayoutError): canvas.rect((0, 1490, 100, 40))
        with self.assertRaises(renderer.LayoutError): canvas.label('runs off the right edge', (1190, 100), 24)
        with self.assertRaisesRegex(renderer.LayoutError, 'Chip row'):
            canvas.chips(['A token row', 'that is far wider', 'than the space it was given'], 100, 100, 200)

    def test_too_many_tokens_fail_instead_of_being_dropped(self):
        spec = self.live_of('gate')
        spec['evidence'] = ['A very long piece of evidence'] * 4
        with self.assertRaisesRegex(renderer.LayoutError, 'Chip row'): renderer.render(spec)

    def test_invalid_mappings_and_unreadable_alt_are_rejected(self):
        changes = [dict(slug='../escape'), dict(post='content/posts/../private.md'),
                   dict(post='content/posts/2026-11-18-other-slug.md'), dict(layout='unknown'),
                   dict(layout='flow'), dict(alt='x'*1001), dict(title='An unsupported — dash\nsecond line'),
                   dict(boundary='An en dash – is also refused')]
        for change in changes:
            spec = dict(self.live[0], **change)
            with self.subTest(change=list(change)), self.assertRaises(ValueError):
                renderer.validate_spec(spec)

    def test_invalid_shape_cannot_silently_omit_content(self):
        cases = []
        spec = self.live_of('ledger'); spec['columns'].append('UNRENDERED'); cases.append(spec)
        spec = self.live_of('ledger'); spec['rows'][0]['footnote'] = 'never drawn'; cases.append(spec)
        spec = self.live_of('ledger'); spec['rows'] = spec['rows'][:2]; cases.append(spec)
        spec = self.live_of('gate'); spec['branches'].append(dict(label='MAYBE', tone='go', title='UNRENDERED', detail='x')); cases.append(spec)
        spec = self.live_of('gate'); spec['branches'][0]['tone'] = 'purple'; cases.append(spec)
        spec = self.live_of('route'); spec['steps'].append(copy.deepcopy(spec['steps'][0])); cases.append(spec)
        spec = self.live_of('route'); spec['steps'][1]['aside'] = 'never drawn'; cases.append(spec)
        spec = self.live_of('lanes'); spec['aside']['items'].pop(); cases.append(spec)
        spec = self.live_of('lanes'); del spec['primary']['steps'][0]['ask']; cases.append(spec)
        spec = self.live_of('hub'); spec['nodes'].pop(); cases.append(spec)
        spec = self.live_of('strata'); del spec['crown']; cases.append(spec)
        spec = self.live_of('span'); spec['marker'] = dict(after=2, label='TOO LATE'); cases.append(spec)
        spec = self.live_of('binding'); spec['versions'].pop(); cases.append(spec)
        for spec in cases:
            with self.subTest(layout=spec['layout']), self.assertRaises(ValueError):
                renderer.render(spec)

    def test_batch_preflight_does_not_write_before_later_layout_failure(self):
        good, bad = copy.deepcopy(self.live[:2])
        bad['title'] = 'Will not fit\n' + 'at all ' * 100
        with patch.object(renderer, 'load_specs', return_value=[good, bad]), patch.object(Path, 'write_bytes') as write:
            with self.assertRaises(renderer.LayoutError): renderer.build()
            write.assert_not_called()

    def test_preview_writes_review_copies_and_touches_nothing_committed(self):
        slug = self.live[0]['slug']
        before = renderer.MANIFEST_PATH.read_bytes(); asset = (ROOT/'content/images'/f'{slug}.png').read_bytes()
        with tempfile.TemporaryDirectory() as directory, patch('builtins.print'):
            self.assertIsNone(renderer.build(only=slug, preview=directory))
            with Image.open(Path(directory)/f'{slug}.png') as full, Image.open(Path(directory)/f'{slug}.phone.png') as phone:
                self.assertEqual(full.size, (1200, 1500))
                self.assertEqual(phone.size, (renderer.PHONE_WIDTH, 488))
        self.assertEqual(renderer.MANIFEST_PATH.read_bytes(), before)
        self.assertEqual((ROOT/'content/images'/f'{slug}.png').read_bytes(), asset)


if __name__ == '__main__': unittest.main()
