import time
import psutil
from typing import Tuple
### Selenium and Selenium wire modules
# from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from seleniumwire import webdriver


### BrowserMob Proxy modules
from browsermobproxy import Server as BMPServer
from browsermobproxy.client import Client as BMPClient


def create_chrome_driver(proxy: BMPClient = None) -> webdriver.Chrome:
    options = webdriver.ChromeOptions();
    if proxy != None:
        # dc = webdriver.DesiredCapabilities().CHROME
        options.add_argument("--proxy-server={0}".format(proxy.proxy))
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--headless")

        options.set_capability('applicationCacheEnabled', True)
        options.set_capability('acceptSslCerts', True)
        options.set_capability('proxy', proxy)

    service = ChromeService(executable_path=ChromeDriverManager().install())
    # TODO: Might want ot add a Chrome Profile so state can be used through multiple
    # sessions instead of using a temporary profile
    driver = webdriver.Chrome(service=service, options=options)

    return driver


def create_bmp_proxy() -> Tuple[BMPClient, BMPServer]:
    for proc in psutil.process_iter():
        # check whether the process name matches
        if proc.name() == "browsermob-proxy":
            proc.kill()

    dict = {'port': 9090}
    server = BMPServer(path="./browsermob-proxy/bin/browsermob-proxy", options=dict)
    server.start()
    time.sleep(1)
    proxy = server.create_proxy()
    time.sleep(1)

    return proxy, server


def main() -> None:
    # cache = {}
    # cache_hits = 0

    # Create the setup
    bmp_proxy, bmp_server = create_bmp_proxy();
    driver = create_chrome_driver(bmp_proxy)

    bmp_proxy.new_har("google")
    driver.get("https://www.google.com")
    time.sleep(2)
    print (bmp_proxy.har)

    # for request in driver.requests:
    #     # print(request)
    #     try:
    #         if request.response:
    #             lm = request.response.headers.get('last-modified', None)
    #             if request.url in cache and lm != None and lm == cache[request.url]:
    #                 print("cache hit")
    #                 cache_hits += 1

    #             if lm != None:
    #                 cache[request.url] = lm

    #             print(
    #                     # request.response.url,
    #                     request.response.status_code,
    #                     request.response.reason,
    #                     )
    #             print(request.response.headers)
    #     except:
    #         print("error with response")

    # time.sleep(3)

    # print("===========================")
    # print("Second GET")

    # driver.get('https://www.google.com')

    # for request in driver.requests:
    #     # print(request)
    #     try:
    #         if request.response:
    #             lm = request.response.headers.get('last-modified', None)
    #             if request.url in cache and lm != None and lm == cache[request.url]:
    #                 print("cache hit")
    #                 cache_hits += 1

    #             if lm != None:
    #                 cache[request.url] = lm

    #             print(
    #                     # request.response.url,
    #                     request.response.status_code,
    #                     request.response.reason,
    #                     )
    #             print(request.response.headers)
    #     except:
    #         print("error with response")

    # time.sleep(4)

    # print(cache)
    # print(cache_hits)

    ### close everything
    bmp_server.stop()
    driver.quit()


if __name__ == "__main__":
    main()
