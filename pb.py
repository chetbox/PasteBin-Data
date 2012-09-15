#!/usr/bin/python3

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

def http_request(params, endpoint, method='POST', send_key=True):
    if send_key:
        params = dict(params.items() + [('api_dev_key', API_KEY)])
    req_params = urlencode(params)
    if method == 'GET':
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

def get_paste(id):
    return http_request({
        'i': id,
    }, RAW_ENDPOINT, method='GET', send_key=False)

def get_and_add_paste_content(paste_dict):
    paste_dict = paste_dict.copy()
    paste_dict['paste_content'] = \
        get_paste(paste_dict['paste_key'])
    return paste_dict

def save_thing(thing, file, convert=(lambda x: x)):
    with codecs.open(file, 'wb') as f:
        f.write(convert(thing))

def save_latest_trends():
    save_pastes('data/trends', get_trends())

def save_paste(ppath, p):
    print('---\n' + ppath)
    if not exists(ppath):
        complete = get_and_add_paste_content(p)
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
            continue

        print('---\n' + f)
        complete = get_and_add_paste_content(p)
        save_thing(complete['paste_content'], ppath)


class PasteLinkExtractor(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.in_a = False
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
            if id not in NON_PASTES:
                self.in_a = True
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
