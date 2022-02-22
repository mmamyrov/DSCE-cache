import time
import psutil
import pprint
import json

from browsermobproxy.client import Client as BMPClient
from browsermobproxy.server import Server as BMPServer

from selenium.webdriver.chrome.service import Service as ChromeService
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.devtools import DevTools



class BMPProxyManager:
    __bmp_bin_path = "./browsermob-proxy/bin/browsermob-proxy"

    def __init__(self):
        for proc in psutil.process_iter():
            # check whether the process name matches
            if proc.name() == "browsermob-proxy":
                proc.kill()

        self.__server = BMPServer(BMPProxyManager.__bmp_bin_path)
        self.__client = None

    def start_server(self) -> BMPServer:
        self.__server.start()
        return self.__server

    def start_client(self) -> BMPClient:
        self.__client = self.__server.create_proxy()
        return self.__client

    @property
    def client(self):
        return self.__client

    @property
    def server(self):
        return self.__server

class Har:
    def __init__(self):
        pass

    @staticmethod
    def isCacheEntry(entry):
        if entry.response.status == 304:
            return True

        resBodySize = max(0, entry.response.bodySize)
        return resBodySize == 0 and entry.response.content and entry.response.content.size > 0




def main() -> None:
    proxy = BMPProxyManager()
    server = proxy.start_server()
    client = proxy.start_client()
    capture_options = {
        "captureHeaders": True,
        "captureContent": True,
        "captureBinaryContent": True
    }

    client.new_har("google", options=capture_options)

    options = webdriver.ChromeOptions()
    options.add_argument("--proxy-server={}".format(client.proxy))
    options.add_argument("user-data-dir=/Users/medetm/Library/Application Support/Google/Chrome/Profile 1")

    # options.add_argument("--headless")
    options.set_capability('applicationCacheEnabled', True)
    options.set_capability('acceptSslCerts', True)

    service = ChromeService(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    site = "https://github.com/AutomatedTester/browsermob-proxy-py"

    driver.get(site)
    time.sleep(2)

    driver.get(site)
    time.sleep(3)
    # pprint.pprint(client.har)

    with open('out.har', 'w') as har_file:
        json.dump(client.har, har_file)

    server.stop()
    # while True:
    #     pass
    driver.quit()

# https://github.com/janodvarko/harviewer/blob/579969c6bb5537e0ddb358c6a273325eed16fe18/webapp/scripts/preview/harModel.js#L352
# could use the definition of cacheEntry similar to how HarViewer implements it



if __name__ == "__main__":
    main()
