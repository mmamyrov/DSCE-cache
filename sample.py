import random

alexa10k = []
with open('alexa10k.txt', 'r') as f:
    alexa10k = f.readlines()

output = open("new_sample.txt", "w")

for x in range(50):
    lower_bound = x * 200 # choose one site per 200 in the list
    upper_bound = lower_bound + 199
    output.write(alexa10k[random.randint(lower_bound, upper_bound)])

output.close()
