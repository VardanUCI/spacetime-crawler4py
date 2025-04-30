import os
import logging
from hashlib import sha256
from urllib.parse import urlparse

def get_logger(name, filename=None):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not os.path.exists("Logs"):
        os.makedirs("Logs")
    fh = logging.FileHandler(f"Logs/{filename if filename else name}.log")
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter(
       "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


def get_urlhash(url):
    parsed = urlparse(url)
    return sha256(
        f"{parsed.netloc}/{parsed.path}/{parsed.params}/"
        f"{parsed.query}/{parsed.fragment}".encode("utf-8")).hexdigest()

def normalize(url):
    parsed = urlparse.urlparse(url)
    parsed = parsed._replace(fragment='')
    query_params = urlparse.parse_qs(parsed.query)
    if 'timeline' in parsed.path and 'from' in query_params:
        query_params.pop('from', None)
    
    new_query = urlparse.urlencode(query_params, doseq=True)
    parsed = parsed._replace(query=new_query)
    
    normalized = urlparse.urlunparse(parsed)
    
    if not normalized.endswith('/') and '.' not in normalized.split('/')[-1]:
        normalized += '/'
    
    return normalized
