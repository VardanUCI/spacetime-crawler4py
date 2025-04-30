import re

class Config(object):
    def __init__(self, config):
        self.user_agent = config["IDENTIFICATION"]["USERAGENT"].strip()
        print(self.user_agent)
        assert self.user_agent != "DEFAULT AGENT", "Set useragent in config.ini"
        assert re.match(r"^[a-zA-Z0-9_ ,]+$", self.user_agent), "User agent should not have any special characters outside '_', ',' and 'space'"
        self.threads_count = int(config["LOCAL PROPERTIES"]["THREADCOUNT"])
        self.save_file = config["LOCAL PROPERTIES"]["SAVE"]

        self.host = config["CONNECTION"]["HOST"]
        self.port = int(config["CONNECTION"]["PORT"])

        # Add debug prints here
        print("Raw SEEDURL from config.ini:", config["CRAWLER"]["SEEDURL"])
        self.seed_urls = config["CRAWLER"]["SEEDURL"].split(",")
        print("Parsed seed_urls:", self.seed_urls)

        self.time_delay = float(config["CRAWLER"]["POLITENESS"])

        self.cache_server = None