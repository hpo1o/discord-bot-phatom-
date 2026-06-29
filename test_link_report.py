import unittest

import link_report


class LinkReportTests(unittest.TestCase):
    def test_extracts_and_normalizes_links(self):
        links = link_report.extract_links(
            "See <HTTP://WWW.Example.com/ref/42/#section> "
            "and https://example.com/ref/42."
        )
        self.assertEqual(links, {"https://example.com/ref/42"})

    def test_owner_can_repeat_own_link(self):
        messages = [
            ("100", "https://example.com/ref/owner"),
            ("100", "again https://example.com/ref/owner"),
        ]
        self.assertEqual(link_report.find_eligible_user_ids(messages), ["100"])

    def test_later_user_of_someone_elses_link_is_excluded(self):
        messages = [
            ("100", "https://example.com/ref/shared"),
            ("200", "https://example.com/ref/shared"),
            ("300", "https://example.com/ref/unique"),
        ]
        self.assertEqual(
            link_report.find_eligible_user_ids(messages),
            ["100", "300"],
        )

    def test_any_borrowed_link_disqualifies_user(self):
        messages = [
            ("100", "https://example.com/ref/owner"),
            ("200", "https://example.com/ref/unique"),
            ("200", "https://example.com/ref/owner"),
        ]
        self.assertEqual(link_report.find_eligible_user_ids(messages), ["100"])

    def test_query_parameters_remain_part_of_link_identity(self):
        messages = [
            ("100", "https://example.com/ref?code=one"),
            ("200", "https://example.com/ref?code=two"),
        ]
        self.assertEqual(
            link_report.find_eligible_user_ids(messages),
            ["100", "200"],
        )

    def test_csv_contains_only_one_id_column(self):
        self.assertEqual(
            link_report.build_discord_id_csv(["100", "200"]),
            b"discord_id\n100\n200\n",
        )


if __name__ == "__main__":
    unittest.main()
