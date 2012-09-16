#!/usr/bin/python

API_KEY = '1689f6a86b4705aa739a1874915ee4fd'
SERVER = 'pastebin.com'
API_ENDPOINT = '/api/api_post.php'
RAW_ENDPOINT = '/raw.php'
NON_PASTES = set(['settings'])

import sys
if sys.version_info[0] == 3:
    import html.parser as HTMLParser
    import http.client as httplib
    from urllib.parse import urlencode
else:
    import httplib
    from urllib import urlencode
    from HTMLParser import HTMLParser
from lxml import etree
import codecs
from os.path import exists, dirname, join
from os import makedirs
from glob import glob
import re
from threading import Thread
import time

import paste_filter


def http_request(params, endpoint, method='POST', send_key=True):
    if send_key:
        params = dict(params.items() + [('api_dev_key', API_KEY)])
    req_params = urlencode(params)
    if method == 'GET' and req_params:
        endpoint = endpoint + '?' + req_params
        req_params = ''
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "Accept": "text/plain"
    }
    conn = httplib.HTTPConnection(SERVER)
    conn.request(method, endpoint, req_params, headers)
    response = conn.getresponse()
    return response.read()

def xml_to_dict(paste_xml):
    return dict(map(
            lambda p: (p.tag, p.text),
            paste_xml))

def xml_http_request(*args, **kargs):
    document = etree.fromstring(
        '<pastes>' +
        http_request(*args, **kargs) +
        '</pastes>'
    )
    return document

def get_trends():
    return map(xml_to_dict, xml_http_request({
        'api_option': 'trends'
    }, API_ENDPOINT, method='POST').xpath('//paste'))

def get_paste_content(id):
    return http_request({
        'i': id,
    }, RAW_ENDPOINT, method='GET', send_key=False)

def get_paste_title(id):
    doc = http_request({}, '/%s' % id, method='GET', send_key=False)
    return re.search('<h1>(.*)</h1>', doc, re.DOTALL).group(1)

def read_paste(ppath):
    return eval(
        codecs.open(ppath, 'r', encoding='utf-8').read()
    )

def get_paste(paste_dict, ppath):
    if exists(ppath):
        paste_dict = read_paste(ppath)
    else:
        paste_dict = paste_dict.copy()
    if not paste_dict.has_key('paste_title'):
        paste_dict['paste_title'] = get_paste_title(paste_dict['paste_key'])
    if not paste_dict.has_key('paste_content'):
        paste_dict['paste_content'] = get_paste_content(paste_dict['paste_key'])
    if not paste_dict.has_key('type'):
        paste_dict['type'] = paste_filter.identify(paste_dict['paste_content'])
    if not paste_dict.has_key('keep'):
        paste_dict['keep'] = paste_filter.keep(paste_dict['type'])
    return paste_dict

def save_thing(thing, file, convert=(lambda x: x)):
    with codecs.open(file, 'wb') as f:
        f.write(convert(thing))

def save_latest_trends():
    for p in get_trends():
        save_paste('data/trends', p)

def save_paste(ppath, p):
    if not exists(ppath):
        complete = get_paste(p, ppath)
        if complete['keep']:
            save_thing(complete, ppath, convert=repr)
    else:
        print('Already exists.')

def convert_pastes_to_text(paths):
    for f in glob(paths):
        convert_paste_to_text(f)

def convert_paste_to_text(f):
    p = eval( codecs.open(f, 'r', encoding='utf-8').read() )
    ppath = dirname(f) + '/txt/%s - %s.txt' % (
        p['paste_key'], p['paste_title'] )

    if not exists(dirname(ppath)):
        makedirs(dirname(ppath))

    if exists(ppath):
        return

    complete = get_paste(p, ppath)
    if complete['keep']:
        save_thing(complete['paste_content'], ppath)


class PasteLinkExtractor(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.in_a = False
        self.seen = set()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            attrs_d = dict(attrs)
            if 'href' not in attrs_d:
                return
            
            m = re.match('^/([a-zA-Z0-9]{8})$', attrs_d['href'])
            
            if m is None:
                return
            
            id = m.group(1)
            if id not in NON_PASTES and id not in self.seen:
                self.in_a = True
                self.seen.add(id)
                self.links.append({
                    'paste_key': id,
                })

    def handle_endtag(self, tag):
        if self.in_a:
            self.in_a = False

    def handle_data(self, data):
        if self.in_a:
            self.links[-1]['paste_title'] = data


def get_recent_pastes():
    doc = http_request({}, '/archive', method='GET', send_key=False)
    ple = PasteLinkExtractor()
    ple.feed(doc)
    return ple.links

def save_recent_pastes():
    recent = get_recent_pastes()
    i = 0
    for p in recent:
        print(('%.1f' % (float(i) / float(len(recent)) * 100.0)) + '%')
        ppath = join('data/recent', '%s.repr' % p['paste_key'])
        save_paste(ppath, p)
        convert_paste_to_text(ppath)
        i += 1

def print_paste(p):
    format = p['paste_format_short'] if p.has_key('paste_format_short') else '-' * 8
    print('\n' * 100)
    print('-' * 32)
    print(p['paste_title'])
    print('-' * 32)
    print(p['paste_content'])
    print('--' + ('(%s)' % p['paste_key']) + '--' + format + '-' * 10)

class PastePrinter:

    def __init__(self):
        self.got = set()
        self.to_display = []

    def fetch_more(self):
        recent_pastes = filter(
                lambda p: p['paste_key'] not in self.got,
                get_recent_pastes()
        )

        for p in recent_pastes:
            self.got.add(p['paste_key'])

        for p in recent_pastes:
            ppath = 'data/recent/%s.repr' % p['paste_key']
            paste = get_paste(p, ppath)
            if paste['keep']:
                self.to_display.append(paste)
                save_paste(ppath, paste)
                convert_paste_to_text(ppath)

    def show_next(self):
        if len(self.to_display) > 0:
            next = self.to_display.pop(0)

pp = PastePrinter()
ppt_ok = True

def paste_fetcher():
    global ppt_ok

    while ppt_ok:
        try:
            pp.fetch_more()
            for i in range(60 *5):
                if not ppt_ok:
                    break
                time.sleep()
        except KeyboardInterrupt as e:
            ppt_ok = False

ppt = Thread(target=paste_fetcher)

def start_live_print_feed():
    global ppt_ok

    ppt.start()

    try:
        while ppt_ok:
            pp.show_next()
            for i in range(5):
                if not ppt_ok:
                    break
                time.sleep(1)
    except KeyboardInterrupt as e:
        print(e)
        ppt_ok = False
