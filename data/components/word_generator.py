import os
import json


letters = "abcdefghijklmnopqrstuvwxyz"

def load_words(max_length):
    p = os.path.join("resources", "dictionary.json")
    raw_words = {}
    with open(p, "r") as f:
        words = json.load(f)
        raw_words = {k.lower(): v for k, v in words.items() 
                              if max_length > len(k) > 2 
                              and all((x in letters for x in k.lower()))}
    return raw_words
    