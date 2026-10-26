"""Regression checks for silhouette bleed, clipping and deterministic glyph positions."""
import unittest
import xml.etree.ElementTree as ET

from generate_profile import portrait, portrait_rows, sample_portrait, COLS, ROWS, CELL_W, tech_stack


class PortraitTests(unittest.TestCase):
    def test_wall_is_styled_as_faint_dots_in_ascii(self):
        rows,shades = portrait_rows()
        patch = [rows[y][x] for y in range(8,16) for x in range(8,16)]
        self.assertEqual(set(patch),{'.',' '})
        self.assertTrue(all(shades[y][x] <= 36 for y in range(8,16) for x in range(8,16)))

    def test_every_printed_character_is_inside_the_alpha_silhouette(self):
        _, alpha = sample_portrait()
        rows, _ = portrait_rows()
        printed = [(x,y) for y,row in enumerate(rows) for x,char in enumerate(row) if char != " "]
        self.assertGreater(len(printed), 1000)
        self.assertTrue(all(alpha.getpixel((x,y)) >= 235 for x,y in printed))

    def test_silhouette_has_margin_on_every_side(self):
        rows, _ = portrait_rows()
        printed = [(x,y) for y,row in enumerate(rows) for x,char in enumerate(row) if char != " "]
        self.assertGreaterEqual(min(x for x,y in printed), 4)
        self.assertLessEqual(max(x for x,y in printed), COLS-5)
        self.assertGreaterEqual(min(y for x,y in printed), 3)
        self.assertLessEqual(max(y for x,y in printed), ROWS-4)

    def test_body_ink_has_generous_padding_on_all_sides(self):
        rows,shades = portrait_rows()
        body = [(x,y) for y,row in enumerate(rows) for x,char in enumerate(row)
                if char != ' ' and shades[y][x] > 36]
        self.assertGreaterEqual(min(x for x,y in body),int(COLS*.1))
        self.assertLessEqual(max(x for x,y in body),int(COLS*.9))
        self.assertGreaterEqual(min(y for x,y in body),int(ROWS*.1))
        self.assertLessEqual(max(y for x,y in body),int(ROWS*.9))

    def test_each_glyph_has_a_fixed_cell_position_and_outer_clip(self):
        rows, shades = portrait_rows()
        root = ET.fromstring('<svg>'+portrait(rows,shades,True)+'</svg>')
        clips = root.findall('.//clipPath')
        self.assertIn('portraitViewport',[clip.get('id') for clip in clips])
        for text in root.findall('.//text'):
            spans = text.findall('tspan')
            if not spans:
                continue
            positions = [float(x) for span in spans for x in span.get('x').split()]
            self.assertEqual(positions,[round(20+i*CELL_W,3) for i in range(COLS)])
            self.assertEqual(sum(len(span.text or '') for span in spans),COLS)

    def test_ai_marks_are_real_downloaded_svg_paths(self):
        markup = tech_stack('ai',5)
        root = ET.fromstring(markup)
        ns = {'s':'http://www.w3.org/2000/svg'}
        logos = root.findall('./s:svg',ns)
        self.assertEqual(len(logos),10)
        self.assertTrue(all(logo.findall('.//s:path',ns) for logo in logos))
        self.assertNotIn('>LC<',markup)
        self.assertNotIn('>LG<',markup)

    def test_facial_tones_are_not_collapsed_into_eight_bands(self):
        rows, shades = portrait_rows()
        all_ink = {tone for row,tones in zip(rows,shades) for char,tone in zip(row,tones) if char != ' '}
        self.assertGreater(len(all_ink),150)
        # The middle of the upper half contains the face in this full-bust photo.
        face_ink = {shades[y][x] for y in range(int(ROWS*.22),int(ROWS*.48))
                    for x in range(int(COLS*.37),int(COLS*.62)) if rows[y][x] != ' '}
        self.assertGreater(len(face_ink),90)


if __name__ == '__main__':
    unittest.main()
