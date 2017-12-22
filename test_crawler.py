import crawler

import unittest
from unittest.mock import MagicMock

import os
import logging
import sys


def setup_test_flatshare_db():
    test_filename = 'flatshare_db_test.json'
    crawler.FlatshareDB.FLATSHARE_DB_FILENAME = test_filename
    if os.path.isfile(test_filename):
        os.unlink(test_filename)


def setup_logging_stdout():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    root.addHandler(ch)


class FlatshareDBTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup_test_flatshare_db()

    def test_db(self):
        db = crawler.FlatshareDB()
        db.add('/foo')
        db.add('/bar')
        db.write_db()

        db2 = crawler.FlatshareDB()
        self.assertEqual(db2.exists('/foo'), True)


class MailTest(unittest.TestCase):
    def test_mail(self):
        email = crawler.FlatshareEmail(
                'http://www.google.com',
                'this is a useless <b>EMAIL</b>',
                'NonExistantTestFlatshare')
        crawler.MailSender.send(email)
        print("Check your inbox, you should have received a mail")


class CrawlerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup_test_flatshare_db()
        setup_logging_stdout()

    def test_crawler(self):
        # first crawl initializes the database
        c = crawler.WGCompanyCrawler()
        c._fetch_flatshare_hrefs = MagicMock()
        c._fetch_flatshare_hrefs.return_value = ["foo", "bar"]
        c.crawl()

        c._fetch_flatshare_hrefs.assert_called_once()

        # second crawl fetches new flatshare "qux" and sends mail
        c2 = crawler.WGCompanyCrawler()
        c2._fetch_flatshare_hrefs = MagicMock()
        c2._fetch_flatshare_hrefs.return_value = ["foo", "bar", "&wg=qux"]
        c2._fetch_flatshare_content = MagicMock()
        c2._fetch_flatshare_content.return_value = "This is the content for the qux flatshare"
        c2.crawl()

        c2._fetch_flatshare_hrefs.assert_called_once()
        c2._fetch_flatshare_content.assert_called_once_with("&wg=qux")

        print("Check your inbox, you should have received a mail")


if __name__ == '__main__':
    unittest.main()
        

