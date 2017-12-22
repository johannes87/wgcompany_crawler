#!/usr/bin/env python3

from bs4 import BeautifulSoup
import requests

import json
import os
import time
import sys
import hashlib
import argparse
import re
import logging
import traceback

import smtplib
import email.mime.text
import email.mime.multipart

from configholder import config


class MailSender:
    @staticmethod 
    def send(mimetext):
        s = smtplib.SMTP(config['smtp']['host'], config['smtp']['port'])
        if config['smtp']['use_tls']:
            s.starttls()
        s.login(config['smtp']['username'], config['smtp']['password'])
        s.send_message(mimetext)
        s.quit()


class FlatshareEmail(email.mime.multipart.MIMEMultipart):
    def __init__(self, flatshare_url, flatshare_content, flatshare_name):
        super().__init__()

        self['Subject'] = config['mail']['subject'].format(flatshare_name=flatshare_name)
        self['From'] = config['mail']['from']
        self['To'] = config['mail']['recipients']
        
        url_html = '<a href="{}">{}</a>'.format(flatshare_url, flatshare_url)
        html_content = 'Link: {}<br><br>{}'.format(url_html, flatshare_content)

        part_html = email.mime.text.MIMEText(html_content, 'html')
        self.attach(part_html)
        

class FlatshareDB:
    FLATSHARE_DB_FILENAME = 'flatshare_db.json'

    def __init__(self, initialize=False):
        self._flatshare_db = {}
        if not initialize:
            self._read_db()
    
    def _read_db(self):
        try:
            flatshare_db_file = open(self.FLATSHARE_DB_FILENAME, 'r')
            flatshare_db_json = json.load(flatshare_db_file)
            flatshare_db_file.close()

            for flatshare_href in flatshare_db_json:
                self.add(flatshare_href)
        except FileNotFoundError:
            self._flatshare_db = {}

    def write_db(self):
        flatshare_db_file = open(self.FLATSHARE_DB_FILENAME, 'w')
        json.dump(list(self._flatshare_db.keys()), flatshare_db_file)
        flatshare_db_file.close()
    
    def is_empty(self):
        return len(self._flatshare_db) == 0

    def add(self, href):
        self._flatshare_db[href] = True

    def exists(self, href):
        return href in self._flatshare_db

    def initialize_with_hrefs(self, flatshare_hrefs):
        self._flatshare_db = {}
        for href in flatshare_hrefs:
            self.add(href)

    def find_diff(self, current_flatshare_hrefs):
        new_flatshares_hrefs = []
        for href in current_flatshare_hrefs:
            if not self.exists(href):
                new_flatshares_hrefs.append(href)

        return new_flatshares_hrefs


class WGCompanyCrawler:
    WG_COMPANY_URL = 'http://wgcompany.de'
    SLEEP_AFTER_FLATSHARE_FETCH_SEC = 5.0
    
    def __init__(self, initialize=False):
        self.flatshare_db = FlatshareDB(initialize=initialize)

    def _fetch_flatshare_hrefs(self):
        zquery_data = {
                'st': '1',
                'c': '',
                'a': '',
                'l': config['person']['age'],
                'e': 'egal',
                'm': config['person']['gender'],
                'o': '',
                'sort': 'doe' # sort by entry-date
                }

        flatshare_list_request = requests.post(self.WG_COMPANY_URL + '/cgi-bin/zquery.pl', data=zquery_data)
        flatshare_list_soup = BeautifulSoup(flatshare_list_request.text, 'html5lib')
        flatshare_tr_soup = flatshare_list_soup.find_all('div', id='content')[0].table.find_all('tr')
        flatshare_hrefs = [row.a['href'] for row in flatshare_tr_soup]
        return flatshare_hrefs

    def _fetch_flatshare_content(self, href):
        soup = BeautifulSoup(requests.get(self.WG_COMPANY_URL + href).text, 'html5lib')
        flatshare_content = soup.find_all('div', id='content')[0]
        time.sleep(self.SLEEP_AFTER_FLATSHARE_FETCH_SEC)
        return flatshare_content

    @staticmethod
    def _get_flatshare_name(flatshare_href):
        return re.match('.*&wg=(.*)$', flatshare_href).group(1)

    def crawl(self):
        current_flatshare_hrefs = self._fetch_flatshare_hrefs()

        if self.flatshare_db.is_empty():
            self.flatshare_db.initialize_with_hrefs(current_flatshare_hrefs)
            logging.info('Initialized with {} flatshares'.format(len(current_flatshare_hrefs)))
        else:
            flatshare_hrefs_diff = self.flatshare_db.find_diff(current_flatshare_hrefs) 
            logging.info("Found {} new flatshares".format(len(flatshare_hrefs_diff)))

            for flatshare_href in flatshare_hrefs_diff:
                logging.info("Fetching NEW flatshare (href={})".format(flatshare_href))
                flatshare_content = self._fetch_flatshare_content(flatshare_href)

                logging.info("Sending mail... (href={})".format(flatshare_href))
                flatshare_url = "{}{}".format(self.WG_COMPANY_URL, flatshare_href)
                flatshare_name = self._get_flatshare_name(flatshare_href)
                email = FlatshareEmail(flatshare_url, flatshare_content, flatshare_name)
                MailSender.send(email)

            self.flatshare_db.initialize_with_hrefs(current_flatshare_hrefs)
        
        self.flatshare_db.write_db()


if __name__ == '__main__':
    abspath = os.path.abspath(__file__)
    os.chdir(os.path.dirname(abspath))

    logging.basicConfig(
            filename='crawler.log',
            format='%(asctime)s %(message)s', 
            level=logging.INFO)

    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('-i',
            '--initialize', 
            action='store_true', 
            help='perform initial crawl without sending mails')
        args = parser.parse_args()

        wg_company_crawler = WGCompanyCrawler(args.initialize)
        wg_company_crawler.crawl()
    except Exception:
        logging.error(traceback.format_exc())
        raise
