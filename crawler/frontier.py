import os
import shelve
from threading import Thread, RLock
from queue import Queue, Empty
from utils import get_logger, get_urlhash, normalize
from scraper import is_valid

class Frontier(object):
    def __init__(self, config, restart):
        print("Loading seed URLs:", config.seed_urls)
        print(f"Restart flag: {restart}")
        self.logger = get_logger("FRONTIER")
        self.config = config
        self.to_be_downloaded = list()
        
        print(f"Save file path: {self.config.save_file}")
        print(f"Does save file exist? {os.path.exists(self.config.save_file)}")
        if not os.path.exists(self.config.save_file) and not restart:
            self.logger.info(
                f"Did not find save file {self.config.save_file}, "
                f"starting from seed.")
        elif os.path.exists(self.config.save_file) and restart:
            self.logger.info(
                f"Found save file {self.config.save_file}, deleting it.")
            os.remove(self.config.save_file)
            print("Save file deleted")
        self.save = shelve.open(self.config.save_file)
        print(f"Contents of self.save after opening: {list(self.save.keys())}")
        if restart:
            print("Restart is True, adding seed URLs")
            for url in self.config.seed_urls:
                print(f"Calling add_url for: {url}")
                self.add_url(url)
        else:
            print("Restart is False, parsing save file")
            self._parse_save_file()
            if not self.save:
                for url in self.config.seed_urls:
                    self.add_url(url)

    def _parse_save_file(self):
        total_count = len(self.save)
        tbd_count = 0
        for url, completed in self.save.values():
            if not completed and is_valid(url):
                self.to_be_downloaded.append(url)
                tbd_count += 1
        self.logger.info(
            f"Found {tbd_count} urls to be downloaded from {total_count} "
            f"total urls discovered.")

    def get_tbd_url(self):
        try:
            url = self.to_be_downloaded.pop()
            print(f"Returning URL from to_be_downloaded: {url}")
            return url
        except IndexError:
            print("to_be_downloaded is empty")
            return None

    def add_url(self, url):
        print(f"Inside add_url with: {url}")
        url = normalize(url)
        print(f"Normalized URL: {url}")
        urlhash = get_urlhash(url)
        print(f"URL hash: {urlhash}")
        print(f"Is URL hash in self.save? {urlhash in self.save}")
        if urlhash not in self.save:
            self.save[urlhash] = (url, False)
            self.save.sync()
            self.to_be_downloaded.append(url)
            print(f"URL added to to_be_downloaded: {url}")
    
    def mark_url_complete(self, url):
        urlhash = get_urlhash(url)
        if urlhash not in self.save:
            self.logger.error(
                f"Completed url {url}, but have not seen it before.")
        self.save[urlhash] = (url, True)
        self.save.sync()