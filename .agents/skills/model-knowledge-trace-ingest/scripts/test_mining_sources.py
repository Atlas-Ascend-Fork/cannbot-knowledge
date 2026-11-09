"""Source references remain local to the immutable original mining manifest."""

import copy
import unittest

from mining_sources import all_sources, candidate_sources


class MiningSourceTests(unittest.TestCase):
    def source(self, name):
        return {'normalized_dir': '/synthetic/' + name, 'raw_source_sha256': name * 64,
                'normalized_trace_sha256': name.upper() * 64}

    def test_references_resolve_in_candidate_order_without_mutating_input(self):
        sources = [self.source('a'), self.source('b'), self.source('c')]
        manifest = {'sources': sources, 'candidates': [{'sources': [2, 0]}]}
        original = copy.deepcopy(manifest)
        self.assertEqual([sources[2], sources[0]], candidate_sources(manifest, manifest['candidates'][0]))
        self.assertEqual(sources + [sources[2], sources[0]], all_sources(manifest))
        self.assertEqual(original, manifest)

    def test_explicit_descriptors_and_zero_candidates_remain_supported(self):
        source = self.source('a')
        manifest = {'sources': [source], 'candidates': []}
        self.assertEqual([source], all_sources(manifest))
        self.assertEqual([source], candidate_sources(manifest, {'sources': [source]}))

    def test_invalid_indices_booleans_and_incomplete_descriptors_fail_closed(self):
        manifest = {'sources': [self.source('a')], 'candidates': []}
        for source in [True, False, -1, 1, '0', {}, {'normalized_dir': '/synthetic'}]:
            with self.subTest(source=source), self.assertRaises(ValueError):
                candidate_sources(manifest, {'sources': [source]})
        with self.assertRaises(ValueError):
            candidate_sources(manifest, {'sources': []})


if __name__ == '__main__':
    unittest.main()
