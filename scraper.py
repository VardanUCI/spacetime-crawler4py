import re, json, os
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup


stopWords = set()
try:
    with open("stopwords.txt", "r", encoding="utf-8") as f:
        stopWords = {line.strip().lower() for line in f if line.strip()}
except FileNotFoundError:
    pass


dataReport = {
    "urls_are_unique": set(),
    "longest_one": {"url": "", "word_count": 0},
    "freq_word": {},
    "sub_domains": {}
}

def saveData():
    with open("dataReport.json", "w") as f:
        json.dump({
            "urls_are_unique": list(dataReport["urls_are_unique"]),
            "longest_one": dataReport["longest_one"],
            "freq_word": dataReport["freq_word"],
            "sub_domains": dataReport["sub_domains"]
        }, f, indent=4)

def scraper(url: str, resp):
    parsed = urlparse(url)
    url_nf = parsed._replace(fragment="").geturl()
    dataReport["urls_are_unique"].add(url_nf)

    if resp.status == 200 and getattr(resp.raw_response, "content", None):
        soup = BeautifulSoup(resp.raw_response.content, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        words = text.split()
        wc = len(words)

        if wc > dataReport["longest_one"]["word_count"]:
            dataReport["longest_one"] = {"url": url_nf, "word_count": wc}

        for w in words:
            w = w.lower()
            if w.isalpha() and w not in stopWords:
                dataReport["freq_word"][w] = dataReport["freq_word"].get(w, 0) + 1

        dom = parsed.netloc.lower()
        if dom.endswith(".uci.edu"):
            dataReport["sub_domains"][dom] = dataReport["sub_domains"].get(dom, 0) + 1

    links = extract_next_links(url, resp)
    valid = [l for l in links if is_valid(l)]
    saveData()
    return valid

def extract_next_links(url: str, resp) -> list:
    urls = []
    if resp.status != 200 or not getattr(resp.raw_response, "content", None):
        return urls

    content = resp.raw_response.content
    if len(content) > 1_000_000:
        soup = BeautifulSoup(content, "html.parser")
        if len(soup.get_text().split()) < 50:
            return urls
    soup = BeautifulSoup(content, "html.parser")
    if len(soup.get_text().split()) < 10:
        return urls

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if not href:
            continue
        absu = urljoin(resp.url, href)
        clean, _ = urldefrag(absu)
        urls.append(clean)
    return urls

def is_valid(url: str) -> bool:
    try:
        url, _ = urldefrag(url)
        p = urlparse(url)
        if p.scheme not in ("http", "https"):
            return False

        host, path = p.hostname or "", p.path or ""
        domains = ("ics.uci.edu","cs.uci.edu","informatics.uci.edu","stat.uci.edu")
        if not (any(host.endswith(d) for d in domains) or
                (host == "today.uci.edu" and path.startswith("/department/information_computer_sciences"))):
            return False
        if re.search(r"(login|signin|logout|auth|calendar|event|date|\bpage/\d+|\d+/)", path.lower()):
            return False
        if p.query and re.search(r"(reply.*|page=\d+|sid=)", p.query.lower()):
            return False

        if re.search(
            r"\.(css|js|bmp|gif|jpe?g|ico|png|tiff?|mid|mp2|mp3|mp4|wav|avi|mov|mpeg"
            r"|ram|m4v|mkv|ogg|ogv|pdf|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx"
            r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|epub|dll|cnf"
            r"|tgz|sha1|thmx|mso|arff|rtf|jar|csv|rm|smil|wmv"
            r"|swf|wma|zip|rar|gz)$",
            path.lower()
        ):
            return False

        return True
    except TypeError:
        return False