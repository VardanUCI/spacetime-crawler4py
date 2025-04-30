import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import json
import os

stopWords = set()
with open("StopWordsList.txt", "r") as f:
    stopWords = set(word.strip().lower() for word in f.readlines())

dataReport = {
    "urls_are_unique": set(),
    "longest_one": {"url": "", "word_count": 0},
    "freq_word": {},
    "sub_domains": {}
}

def saveData():
    i = 4
    with open("dataReport.json", "w") as f:
        json.dump({
            "urls_are_unique": list(dataReport["urls_are_unique"]),
            "longest_one": dataReport["longest_one"],
            "freq_word": dataReport["freq_word"],
            "sub_domains": dataReport["sub_domains"]
        }, f, indent=i)


def scraper(url, resp):
    print(f"Scraping URL: {url}")
    parsed = urlparse(url)
    urlWithoutFragment = parsed._replace(fragment='').geturl()
    dataReport["urls_are_unique"].add(urlWithoutFragment)  # Fixed key

    if resp.status == 200 and resp.raw_response and resp.raw_response.content:
        objSoup = BeautifulSoup(resp.raw_response.content, "html.parser")
        text = objSoup.get_text(strip=True)
        words = text.split()
        word_count = len(words)

        if word_count > dataReport["longest_one"]["word_count"]:  # Fixed key
            dataReport["longest_one"] = {"url": url, "word_count": word_count}

        for word in words:
            word = word.lower()
            if word.isalpha() and word not in stopWords:  # Fixed variable name
                dataReport["freq_word"][word] = dataReport["freq_word"].get(word, 0) + 1  # Fixed key

        domain = parsed.netloc.lower()
        if domain.endswith(".uci.edu"):
            subdomain = domain
            dataReport["sub_domains"][subdomain] = dataReport["sub_domains"].get(subdomain, 0) + 1  # Fixed key

    links = extract_next_links(url, resp)
    validLinks = []
    for link in links:
        if is_valid(link):
            validLinks.append(link)

    saveData()
    return validLinks


def extract_next_links(url, resp):
    print(f"Extracting links from {url}, status: {resp.status}")
    if resp.status != 200 or not resp.raw_response or not resp.raw_response.content:
        return list()

    if len(resp.raw_response.content) == 0:
        return list()

    if len(resp.raw_response.content) > 1000000:
        objSoup = BeautifulSoup(resp.raw_response.content, "html.parser")
        text = objSoup.get_text(strip=True)
        if len(text.split()) < 50:
            return list()

    objSoup = BeautifulSoup(resp.raw_response.content, "html.parser")
    text = objSoup.get_text(strip=True)
    if len(text.split()) < 10:
        return list()

    listLinks = []
    for charTag in objSoup.find_all("a", href=True):
        atr_href = charTag["href"].strip()
        if atr_href:
            absUrl = urljoin(url, atr_href)
            listLinks.append(absUrl)
    return listLinks


def is_valid(url):
    try:
        print(f"Checking URL: {url}")
        parsed = urlparse(url)
        url = parsed._replace(fragment='').geturl()
        parsed = urlparse(url)

        if parsed.scheme not in set(["http", "https"]):
            return False

        domains = [
            "ics.uci.edu",
            "cs.uci.edu",
            "informatics.uci.edu",
            "stat.uci.edu",
            "today.uci.edu"
        ]
        domain = parsed.netloc.lower()
        if not any(domain == allowed or domain.endswith("." + allowed) for allowed in domains):
            return False

        if domain == "today.uci.edu" or domain.endswith(".today.uci.edu"):
            if not parsed.path.startswith("/department/information_computer_sciences"):
                return False

        if re.search(r"(login|signin|logout|auth|calendar|event|date|page/[0-9]+|[0-9]+/)", parsed.path.lower()):
            return False

        if parsed.query and re.search(r"(reply.*|page=[0-9]+|sid=)", parsed.query.lower()):
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print("TypeError for ", parsed)
        raise