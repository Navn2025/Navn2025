from datetime import date
import unittest
import xml.etree.ElementTree as ET

from update_insights import summarize, weekly_values, language_card, svg, activity_series, activity_chart


class InsightsTests(unittest.TestCase):
    def test_fork_stars_and_languages_are_excluded(self):
        repos = [{"fork":False,"language":"Python","stargazers_count":3,"forks_count":2},
                 {"fork":False,"language":None,"stargazers_count":1,"forks_count":0},
                 {"fork":True,"language":"Rust","stargazers_count":999,"forks_count":999}]
        result = summarize({"followers":8},repos)
        self.assertEqual(result["stars"],4)
        self.assertEqual(result["forks"],2)
        self.assertEqual(result["public_repos"],3)
        self.assertEqual(result["languages"],[{"name":"Python","count":1}])
        self.assertEqual(result["language_repos"],1)

    def test_weekly_bins_preserve_total_and_use_sundays(self):
        days = [{"date":"2026-10-24","count":4},{"date":"2026-10-25","count":3},{"date":"2026-10-26","count":2}]
        weeks = weekly_values(days)
        self.assertEqual(weeks,[(date(2026,10,18),4),(date(2026,10,25),5)])
        self.assertEqual(sum(value for _,value in weeks),9)

    def test_empty_language_chart_is_valid_and_has_no_invented_data(self):
        output = svg(492,360,"Empty",language_card({"languages":[],"language_repos":0}))
        ET.fromstring(output)
        self.assertNotIn("nan",output.lower())
        self.assertNotIn("100.0%",output)

    def test_activity_cap_and_average_preserve_real_counts(self):
        days = [{"date":f"2026-10-{day:02}","count":count} for day,count in [(4,10),(11,10),(18,10000),(25,10)]]
        before = [dict(day) for day in days]
        weeks,averages,cap,window = activity_series(days,{"maximum_cap":40})
        self.assertEqual(days,before)
        self.assertEqual(sum(value for _,value in weeks),10030)
        self.assertEqual(averages[:2],[10,10])
        self.assertEqual(window,3)
        self.assertEqual(cap,40)
        output = activity_chart({"days":days,"generated_at":"2026-10-26"},{"maximum_cap":40})
        root = ET.fromstring(output)
        points = root.findall('.//{http://www.w3.org/2000/svg}circle')
        self.assertTrue(all(63 <= float(p.get('cy')) <= 191 for p in points))
        self.assertIn('10000 actual contributions',output)

    def test_empty_and_zero_activity_do_not_divide_by_zero(self):
        for days in [[],[{"date":"2026-10-26","count":0}]]:
            _,averages,cap,_ = activity_series(days)
            self.assertEqual(cap,20)
            self.assertTrue(all(value == 0 for value in averages))
            ET.fromstring(activity_chart({"days":days,"generated_at":"2026-10-26"}))

    def test_bad_counts_and_configuration_are_rejected(self):
        for count in [-1,float('inf'),float('nan')]:
            with self.assertRaises(ValueError):
                activity_series([{"date":"2026-10-26","count":count}])
        with self.assertRaises(ValueError):
            activity_series([],{"window_weeks":0})


if __name__ == "__main__":
    unittest.main()
