# from selenium import webdriver
from seleniumwire import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from browsermobproxy import Server
from os.path import isfile, join
import os
import time
import json
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


project_path=os.path.dirname(os.path.abspath(__file__))
print (project_path)
desired_capabilities = DesiredCapabilities.CHROME
desired_capabilities["goog:loggingPrefs"] = {"performance": "ALL"}
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--ignore-ssl-errors=yes")
options.add_argument("--ignore-certificate-errors")
options.add_argument("user-data-dir=/Users/rashnakumar/Library/Application Support/Google/Chrome/Default")
# options.add_argument("--no-cache")
seleniumwire_options = {
'disable_capture': True,
}
dict={'port':8090}
server = Server(path=join(project_path, "browsermob-proxy-2.1.4", "bin", "browsermob-proxy"),options=dict)
server.start()
proxy = server.create_proxy(params={"trustAllServers": "true"})
options.add_argument("--proxy-server={}".format(proxy.proxy))	
driver = webdriver.Chrome(ChromeDriverManager().install(),options=options,seleniumwire_options=seleniumwire_options)



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

if __name__ == "__main__":
	# setting the driver's response_interceptor to equal
	# the customised interceptor
	# driver.response_interceptor = interceptor
	sites=["www.spotify.com"]
	for site in sites:
		for x in range(2):
			print ("run ",x)
			driver.get("https://"+site)
			time.sleep(15)
			# Gets all the logs from performance in Chrome
			logs = driver.get_log("performance")

			# Opens a writable JSON file and writes the logs in it
			with open("scripts/network_log_"+str(x)+".json", "w", encoding="utf-8") as f:
				f.write("[")

				# Iterates every logs and parses it using JSON
				for log in logs:
					network_log = json.loads(log["message"])["message"]

					# Checks if the current 'method' key has any
					# Network related value.
					if("Network.response" in network_log["method"]
					        or "Network.request" in network_log["method"]
					        or "Network.webSocket" in network_log["method"]):

					    
						f.write(json.dumps(network_log)+",")
				f.write("{}]")


			# Read the JSON File and parse it using
			# json.loads() to find the urls containing images.
			json_file_path = "network_log.json"
			with open(json_file_path, "r", encoding="utf-8") as f:
				logs = json.loads(f.read())

			# Iterate the logs
			for log in logs:

				# Except block will be accessed if any of the
				# following keys are missing.
				try:
					# URL is present inside the following keys
					url = log["params"]["request"]["url"]

					# Checks if the extension is .png or .jpg
					if url[len(url)-4:] == ".png" or url[len(url)-4:] == ".jpg":
						print(url, end='\n\n')
				except Exception as e:
				    pass
