import time
import psutil
import pprint
import json
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from browsermobproxy.client import Client as BMPClient
from browsermobproxy.server import Server as BMPServer

# from selenium.webdriver.chrome.service import Service as ChromeService
from seleniumwire import webdriver
# from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import os
from os.path import isfile, join
from haralyzer import HarParser, HarPage


# from selenium.webdriver.devtools import DevTools

project_path=os.path.dirname(os.path.abspath(__file__))


class BMPProxyManager:
    # dict={'port':8090}
    __bmp_bin_path = path=join(project_path, "browsermob-proxy-2.1.4", "bin", "browsermob-proxy")

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


customMaxAge=0 #set the custom max-age

def interceptor(request,response):
    # del response.headers['Referer']  # Delete the header first
    try:
        if "max-age" in response.headers["cache-control"]:
            CP=response.headers["cache-control"].split("max-age")
            print (response.headers["cache-control"])
            del response.headers["cache-control"]
            resp=""
            for x in range(len(CP)-1):
                resp+=CP[x]
            response.headers["cache-control"]=resp+"max-age="+str(customMaxAge)
            print (response.headers["cache-control"]+"\n")
    except:
        a=1
    
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
    desired_capabilities = DesiredCapabilities.CHROME
    desired_capabilities["goog:loggingPrefs"] = {"performance": "ALL"}
    options = webdriver.ChromeOptions()
    options.add_argument("--proxy-server={}".format(client.proxy))
    options.add_argument("user-data-dir=/Users/rashnakumar/Library/Application Support/Google/Chrome/Default")
    sw_options = {
        'disable_encoding': True,  # Ask the server not to compress the response
        'enable_har': True
    }

    # options.add_argument("--headless")
    options.set_capability('applicationCacheEnabled', True)
    options.set_capability('acceptSslCerts', True)

    # service = ChromeService(executable_path=ChromeDriverManager().install())
    # driver = webdriver.Chrome(service=service, options=options)
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    driver = webdriver.Chrome(ChromeDriverManager().install(),options=options,seleniumwire_options=sw_options)

    driver.response_interceptor = interceptor

    site = "https://github.com/AutomatedTester/browsermob-proxy-py"

    driver.get(site)
    time.sleep(2)

    driver.get(site)
    time.sleep(3)
    # pprint.pprint(client.har)
    a=driver.har
    b=json.loads(a)
    with open('out.har', 'w') as har_file:
        json.dump(b, har_file)

    with open('out.har', 'r') as f:
        har_parser = HarParser(json.loads(f.read()))

    data = har_parser.har_data
    with open("outHar.json", 'w') as fp:
        json.dump(data, fp)

    

    server.stop()
    # while True:
    #     pass
    driver.quit()

# https://github.com/janodvarko/harviewer/blob/579969c6bb5537e0ddb358c6a273325eed16fe18/webapp/scripts/preview/harModel.js#L352
# could use the definition of cacheEntry similar to how HarViewer implements it



if __name__ == "__main__":
    main()