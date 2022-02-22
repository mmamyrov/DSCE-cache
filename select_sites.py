import random

alexa10k = []
with open('alexa10k.txt', 'r') as f:
    alexa10k = f.readlines()

output = open("sample.txt", "w")

for x in range(50):
    output.write(alexa10k[random.randint(0, len(alexa10k)-1)])

output.close()