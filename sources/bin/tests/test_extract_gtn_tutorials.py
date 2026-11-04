import os
import sys
import tempfile
import unittest
from typing import (
    Any,
    Dict,
    List,
)

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from extract_gtn_tutorials import (
    add_status,
    curate_tutorials,
    export_tutorials_to_tsv,
    filter_tutorials,
    STATUS_COLUMNS,
    TUTORIAL_COLUMNS,
)


def make_tuto(title: str, purl: str, tags: List[str]) -> Dict[str, Any]:
    return {"title": title, "purl": purl, "tags": tags}


class TestFilterTutorials(unittest.TestCase):
    def setUp(self) -> None:
        self.tutos = [
            make_tuto("Assembly", "gxy.io/GTN:T1", ["assembly"]),
            make_tuto("Ecology", "gxy.io/GTN:T2", ["ecology"]),
            make_tuto("No tags", "gxy.io/GTN:T3", []),
        ]

    def test_no_tags_keeps_all(self) -> None:
        """Used by extract_all_tutorials.sh: no tags means all tutorials"""
        self.assertEqual(len(filter_tutorials(self.tutos, None)), 3)
        self.assertEqual(len(filter_tutorials(self.tutos, [])), 3)

    def test_dict_input(self) -> None:
        tutos = {t["purl"]: t for t in self.tutos}
        self.assertEqual(len(filter_tutorials(tutos, None)), 3)

    def test_tags(self) -> None:
        filtered = filter_tutorials(self.tutos, ["ecology"])
        self.assertEqual([t["title"] for t in filtered], ["Ecology"])

    def test_status_is_added(self) -> None:
        status = pd.DataFrame(
            [["Ecology", "Ecology", "gxy.io/GTN:T2", "", True, False]],
            columns=STATUS_COLUMNS,
        )
        filtered = filter_tutorials(self.tutos, ["ecology", "assembly"], status)
        by_title = {t["title"]: t for t in filtered}
        self.assertTrue(by_title["Ecology"]["To keep"])
        self.assertFalse(by_title["Ecology"]["Deprecated"])
        self.assertIsNone(by_title["Assembly"]["To keep"])


class TestAddStatus(unittest.TestCase):
    def test_match_by_permanent_link_not_title(self) -> None:
        """Titles are not unique in the GTN (e.g. 'Galaxy Interactive Tools')"""
        status = pd.DataFrame(
            [
                ["Admin", "Galaxy Interactive Tools", "gxy.io/GTN:T1", "", False, True],
                ["Intro", "Galaxy Interactive Tools", "gxy.io/GTN:T2", "", True, False],
            ],
            columns=STATUS_COLUMNS,
        )
        tuto = make_tuto("Galaxy Interactive Tools", "gxy.io/GTN:T2", [])
        add_status(tuto, status)
        self.assertTrue(tuto["To keep"])
        self.assertFalse(tuto["Deprecated"])

    def test_match_by_title_for_old_status_files(self) -> None:
        """Status files created before the permanent link column was added"""
        status = pd.DataFrame(
            [["Assembly", 'A "quoted" title', "", True, False]],
            columns=["Topic", "Title", "Last modification", "To keep", "Deprecated"],
        )
        tuto = make_tuto('A "quoted" title', "gxy.io/GTN:T1", [])
        add_status(tuto, status)
        self.assertTrue(tuto["To keep"])

    def test_no_match(self) -> None:
        tuto = make_tuto("Unknown", "gxy.io/GTN:T9", [])
        add_status(tuto, pd.DataFrame(columns=STATUS_COLUMNS))
        self.assertIsNone(tuto["To keep"])
        self.assertIsNone(tuto["Deprecated"])


class TestCurateTutorials(unittest.TestCase):
    def test_only_to_keep(self) -> None:
        status = pd.DataFrame(
            [
                ["T", "Keep", "gxy.io/GTN:T1", "", True, False],
                ["T", "Drop", "gxy.io/GTN:T2", "", False, False],
            ],
            columns=STATUS_COLUMNS,
        )
        tutos = [make_tuto("Keep", "gxy.io/GTN:T1", []), make_tuto("Drop", "gxy.io/GTN:T2", [])]
        self.assertEqual([t["title"] for t in curate_tutorials(tutos, status)], ["Keep"])


class TestExportTutorialsToTsv(unittest.TestCase):
    def test_empty_writes_header(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fp = os.path.join(tmp, "tutorials.tsv")
            export_tutorials_to_tsv([], fp)
            df = pd.read_csv(fp, sep="\t")
            self.assertEqual(list(df.columns), TUTORIAL_COLUMNS)
            self.assertEqual(len(df), 0)


if __name__ == "__main__":
    unittest.main()
