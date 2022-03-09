import random
import requests

alexa10k = []
with open('alexa10k.txt', 'r') as f:
    alexa10k = f.readlines()

output = open('sample.txt', 'w')

num_sites = 0

while num_sites < 50:
    lower_bound = num_sites * 200 # choose one site per 200 in the list
    upper_bound = lower_bound + 199

    site = alexa10k[random.randint(lower_bound, upper_bound)].split(',')[1]
    url = 'https://' + site.strip()
    
    try:
        response = requests.head(url)
        if str(response.status_code).startswith('4') or str(response.status_code).startswith('5'):
            valid = False
        else:
            valid = True
    except requests.ConnectionError:
        valid = False

    if valid:
        output.write(url)
        output.write('\n')
        num_sites += 1
    else:
        continue

output.close()
