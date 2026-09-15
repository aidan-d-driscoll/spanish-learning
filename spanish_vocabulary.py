"""

I'll give you two lists, first a base list of Spanish words and definitions, and a list of new Spanish terms and definitions that I have compiled.

Take the second list, the shorter new one, and correct it for me. Fix typos, include missing accents, improve on definitions (the english side can be as many words, semi colons, parentheses as needed to give a full defini3tion), add el/la for nouns, add o/a for gendered words, expand on phrases, etc. 

Output a unique section, showing all new words and definitions (separated by a colon), that the new list had and the base one didn't. Also output a duplicate section, hosting anything that existed in the base, if present.

"""

import random

with open("spanish-vocabulary.txt", "r", encoding="utf-8") as f:
    pairs = [line.split(":") for line in f]
for i in range(len(pairs)):
    pairs[i][0] = pairs[i][0].strip()
    pairs[i][1] = pairs[i][1].strip()

while pairs:
    pair = random.choice(pairs)
    input(pair[0] + " > ")
    print(pair[1])
    pairs.remove(pair)
    print(len(pairs))
    input()