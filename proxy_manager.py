import time
import psutil
import pprint
from browsermobproxy.client import Client as BMPClient
from browsermobproxy.server import Server as BMPServer

from selenium.webdriver.chrome.service import Service as ChromeService
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager


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



def main() -> None:
    proxy = BMPProxyManager()
    server = proxy.start_server()
    client = proxy.start_client()
    client.new_har("google")

    options = webdriver.ChromeOptions()
    options.add_argument("--proxy-server={}".format(client.proxy))
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

    pprint.pprint(client.har)

    server.stop()
    # while True:
    #     pass
    driver.quit()

# https://github.com/janodvarko/harviewer/blob/579969c6bb5537e0ddb358c6a273325eed16fe18/webapp/scripts/preview/harModel.js#L352
# could use the definition of cacheEntry similar to how HarViewer implements it



if __name__ == "__main__":
    main()
