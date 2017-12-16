from urllib.request import urlopen
from bs4 import BeautifulSoup
from urllib import parse
from urllib.parse import urlparse
from queue import *
import threading
import time

max_time = 1800
time_start = time.time()
links = set()
crawled = set()

class Node:
    def __init__(self, label=None, data=None):
        self.label = label
        self.data = data
        self.children = dict()

    def addChild(self, key, data=None):
        if not isinstance(key, Node):
            self.children[key] = Node(key, data)
        else:
            self.children[key.label] = key

    def __getitem__(self, key):
        return self.children[key]


class Trie:
    def __init__(self):
        self.head = Node()

    def __getitem__(self, key):
        return self.head.children[key]

    def add(self, word):
        current_node = self.head
        word_finished = True

        for i in range(len(word)):
            if word[i] in current_node.children:
                current_node = current_node.children[word[i]]
            else:
                word_finished = False
                break

        # For ever new letter, create a new child node
        if not word_finished:
            while i < len(word):
                current_node.addChild(word[i])
                current_node = current_node.children[word[i]]
                i += 1

        # Let's store the full word at the end node so we don't need to
        # travel back up the tree to reconstruct the word
        current_node.data = word

    def has_word(self, word):
        if word == '':
            return False
        if word == None:
            raise ValueError('Trie.has_word requires a not-Null string')

        # Start at the top
        current_node = self.head
        exists = True
        for letter in word:
            if letter in current_node.children:
                current_node = current_node.children[letter]
            else:
                exists = False
                break

        # Still need to check if we just reached a word like 't'
        # that isn't actually a full word in our dictionary
        if exists:
            if current_node.data == None:
                exists = False

        return exists

    def getData(self, word):
        """ This returns the 'data' of the node identified by the given word """
        if not self.has_word(word):
            raise ValueError('{} not found in trie'.format(word))

        # Race to the bottom, get data
        current_node = self.head
        for letter in word:
            current_node = current_node[letter]
        return current_node.data

def trade_spider():
    global flag
    global links_crawled
    while True:
        url = q.get()
        crawled.add(url)
        if len(crawled) == links_crawled:
            print('time taken to crawl ' + str(links_crawled) + ' is ' + str(time.time()-time_start) + ' secs')
            f = open('total_links.txt', 'a')
            f.write('time taken to crawl ' + str(links_crawled) + ' is ' + str(time.time()-time_start) + ' secs \n')
            f.close()
            links_crawled += 1000
        print(threading.current_thread().name + ' now crawling : ' + url )
        try:
            source_code = urlopen(url)
        except:
            print('Could not crawl : ' + url)
            continue
        try:
            plain_text = source_code.read()
        except:
            print('Could not crawl : ' + url)
            continue
        try:
            plain_text = plain_text.decode('utf-8')
        except:
            print('Could not crawl : ' + url)
            continue
        try:
            soup = BeautifulSoup(plain_text, "lxml")
        except:
            print('Could not crawl : ' + url)
            continue
        for link in soup.findAll('a'):
            try:
                href = link.get('href')
                if href[:1] != '#' and href.find('?:action') == -1 and href.find('html#') == -1 and href.find('?%3Aaction') == -1 and href.find('javascript:;')==-1:
                    dom = get_domain_name(href)
                    if dom == domain:
                        href = parse.urljoin(url_base, link.get('href'))
                        href = href.replace('https://', 'http://')
                        if trie.has_word(href) == False:
                            q.put(href)
                            if href != url:
                                links.add(href)
                trie.add(href)
            except:
                continue
        update_file(links)
        links.clear()
        print('crawled : ' + str(len(crawled)))
        if threading.current_thread().name == 'MainThread':
            break

def update_file(links):
    f = open('i_list.txt', 'a')
    for a_link in links:
        f.write(a_link + '\n')
    f.close()

def get_domain_name(url):
    try:
        results = get_sub_domain_name(url).split('.')
        return results[-3] + '.' + results[-2] + '.' + results[-1]
    except:
        return ''

def get_sub_domain_name(url):
    try:
        return urlparse(url).netloc
    except:
        return ''

def threads():
    for _ in range(15):
        t = threading.Thread(target=trade_spider)
        t.start()

url_base = input('Enter the base url : ')
f = open('i_list.txt', 'w')
f.write(url_base + '\n')
f.close()
trie = Trie()
trie.add(url_base)
q = Queue()
q.put(url_base)
flag = 0
links_crawled = 1000
domain = get_domain_name(url_base)
trade_spider()
threads()