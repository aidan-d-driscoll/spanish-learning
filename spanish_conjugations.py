import json
import random

ADD_VERBS = 0
QUIZ_USER = 1

def main():
    with open("spanish-conjugations.json", "r", encoding="utf8") as f:
        verbs_dict = json.load(f)
    verbs = list(verbs_dict.keys())

    if MODE == ADD_VERBS:
        verb = input("Infinitive (-1 to Quit) > ")
        if verb == "-1":
            return
        if verb not in verbs:
            verbs_dict = verbs_dict | add_verb(verb)
        else:
            print("Verb already stored in database.")

        with open("spanish-conjugations.json", "w", encoding="utf8") as f:
            json.dump(verbs_dict, f, indent=2)

    elif MODE == QUIZ_USER:

        moods = ["indicative", "indicative", "indicative", "indicative", "subjunctive", "subjunctive", "subjunctive", "imperative"]
        tenses_indicative = ["present", "preterite", "imperfect", "conditional", "future"]
        tenses_subjunctive = ["present", "imperfect", "future"]
        tenses_imperative = ["affirmative", "negative"]
        conjugations = ["yo", "tú", "él/ella/Ud.", "nosotros", "ellos/ellas/Uds."]
        while verbs:
            verb = random.choice(verbs)
            verbs.remove(verb)
            input(f"\nWhat's the defintion of {verb}? > ")
            print(f"Definition of {verb}: {verbs_dict[verb]['definition']}")
            input(f"\nWhat are the past and present participles of {verb}? > ")
            print(f"Past Participle: {verbs_dict[verb]['past participle']}\nPresent Participle: {verbs_dict[verb]['present participle']}")
            for _ in range(NUM_PER_VERB):
                mood = random.choice(moods)
                if mood == "indicative":
                    tense = random.choice(tenses_indicative)
                    conjugation = random.choice(conjugations)
                elif mood == "subjunctive":
                    tense = random.choice(tenses_subjunctive)
                    conjugation = random.choice(conjugations)
                elif mood == "imperative":
                    tense = random.choice(tenses_imperative)
                    conjugation = random.choice(conjugations[1:])
                input(f"\nWhat is the {mood} {tense} {conjugation} conjugation of {verb}? > ")
                print(f"The correct conjugation is: {verbs_dict[verb][mood][tense][conjugation]}")

def add_verb(verb: str) -> dict:

    definition = input(f"Definition of {verb} > ")
    present_part = input("Present participle > ")
    past_part = input("Past participle > ")

    conjugations = ["yo", "tú", "él/ella/Ud.", "nosotros", "ellos/ellas/Uds."]

    verb_dict = {
        verb: {
            "definition": definition,
            "present participle": present_part,
            "past participle": past_part,
            "indicative": {
                "present": {conjugation: input(f"Indicative Present ({conjugation}) > ") for conjugation in conjugations},
                "preterite": {conjugation: input(f"Indicative Preterite ({conjugation}) > ") for conjugation in conjugations},
                "imperfect": {conjugation: input(f"Indicative Imperfect ({conjugation}) > ") for conjugation in conjugations},
                "conditional": {conjugation: input(f"Indicative Conditional ({conjugation}) > ") for conjugation in conjugations},
                "future": {conjugation: input(f"Indicative Future ({conjugation}) > ") for conjugation in conjugations}
            },
            "subjunctive": {
                "present": {conjugation: input(f"Subjunctive Present ({conjugation}) > ") for conjugation in conjugations},
                "imperfect": {conjugation: input(f"Subjunctive Imperfect ({conjugation}) > ") for conjugation in conjugations},
                "future": {conjugation: input(f"Subjunctive Future ({conjugation}) > ") for conjugation in conjugations}
            },
            "imperative": {
                "affirmative": {conjugation: input(f"Imperative Affirmative ({conjugation}) > ") for conjugation in conjugations if conjugation != "yo"},
                "negative": {conjugation: input(f"Imperative Negative ({conjugation}) > ") for conjugation in conjugations if conjugation != "yo"},
            }
        }
    }

    return verb_dict

if __name__ == "__main__":
    MODE = QUIZ_USER
    NUM_PER_VERB = 3
    main()