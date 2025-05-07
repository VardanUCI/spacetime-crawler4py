import re, json, os
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
from dupDetector import dupDetector, K
from datetime import date, datetime

stopWords = set()
try:
    with open("StopWordsList.txt", "r", encoding="utf-8") as f:
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
    try:
        with open("dataReport.json", "w") as f:
            json.dump({
                "urls_are_unique": list(dataReport["urls_are_unique"]),
                "longest_one": dataReport["longest_one"],
                "freq_word": dataReport["freq_word"],
                "sub_domains": dataReport["sub_domains"]
            }, f, indent=4)
    except OSError as e:
        with open("Logs/Worker.log", "a") as f:
            f.write(f"Error can't save dataReport.json: {e}\n")

def scraper(url: str, resp):
    parsed = urlparse(url)
    url_nf = parsed._replace(fragment="").geturl()
    dataReport["urls_are_unique"].add(url_nf)

    if resp.status == 200 and getattr(resp.raw_response, "content", None):
        soup = BeautifulSoup(resp.raw_response.content, "lxml")
        text = soup.get_text(separator=" ", strip=True)
        if dupDetector(text):
            with open("Logs/Worker.log", "a") as f:
                f.write(f"Let's skip {url_nf}: its duplicate\n")
            return []

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
            if dom.startswith("www."):
                dom = dom[4:]
            dataReport["sub_domains"][dom] = dataReport["sub_domains"].get(dom, 0) + 1
            with open("Logs/Worker.log", "a") as f:
                f.write(f"sub_domain: {dom}, num: {dataReport['sub_domains'][dom]}\n")

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
        soup = BeautifulSoup(content, "lxml")
        if len(soup.get_text().split()) < 50:
            with open("Logs/Worker.log", "a") as f:
                f.write(f"Let's skip {url}: big file and few words\n")
            return urls

    soup = BeautifulSoup(content, "lxml")
    if len(soup.get_text().split()) < 5:
        with open("Logs/Worker.log", "a") as f:
                f.write(f"Let's skip {url}: fewer than five words\n")
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
        domains = ("ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu")
        if not (any(host.endswith(d) for d in domains) or
                (host == "today.uci.edu" and path.startswith("/department/information_computer_sciences"))):
            return False

        if re.search(r"(login|signin|logout|auth|calendar)", path.lower()):
            return False

        if p.query and re.search(r"(reply.*|sid=)", p.query.lower()):
            return False

        date_match = re.search(r"/(\d{4})/(\d{2})/(\d{2})/", path)
        if date_match:
            year, month, day = map(int, date_match.groups())
            try:
                url_date = datetime(year, month, day).date()
                today = date.today()
                if url_date > today or url_date < date(2010, 1, 1):
                    with open("Logs/Worker.log", "a") as f:
                        f.write(f"Let's skip {url}: date is out of range ({url_date})\n")
                    return False
            except ValueError:
                pass

        if re.search(r"page/\d+", path.lower()) or re.search(r"page=\d+", p.query.lower()):
            page_num = re.search(r"\d+", path.lower() + p.query.lower())
            if page_num and int(page_num.group()) > 50:
                with open("Logs/Worker.log", "a") as f:
                    f.write(f"Let's skip {url}: depth exceed\n")
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

        if path.count("/") > 10:
            with open("Logs/Worker.log", "a") as f:
                f.write(f"Let's skip {url}: out of depth limit\n")
            return False

        return True
    except TypeError:
        return False