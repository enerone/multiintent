# Prompt used: I want a tool that searches intent opportunities in the client prompt

import re
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

def find_intents(prompt):
    keywords = ['intent', 'goal', 'target', 'requirement', 'priority']
    stop_words = set(stopwords.words('english'))
    intents = {'intent': [], 'goal': [], 'target': [], 'requirement': [], 'priority': []}
    
    tokens = word_tokenize(prompt.lower())
    for token in tokens:
        if re.match(r'^\W*', token) or len(token.strip()) == 0:
            continue
        for intent, keywords_list in intents.items():
            if any(keyword in keyword_list for keyword, keyword_list in zip([token], [keywords])):
                tokens.remove(token)
                break
    
    grouped_intents = {}
    for token in tokens:
        lower_token = token.lower()
        if lower_token == 'intent':
            continue
        for intent, keywords_list in intents.items():
            if any(lower_token in keyword_list for keyword_list in [keywords] if isinstance(keywords_list, list)):
                if lower_token not in grouped_intents.get(intent, set()):
                    grouped_intents[intent].add(lower_token)
    
    result = [intent for intent in ['intent', 'goal', 'target', 'requirement', 'priority'] if grouped_intents.get(intent, set())]
    return sorted(result)