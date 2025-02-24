# Prompt utilizado: quiero un intento que use lenguage natural para identificar los distintos intentos posibles en el prompt del cliente

import spacy
from spacy.lang.en import en_core_web_sm
from nltk.tokenize import word_tokenize, ngrams
from nltk import pos_tag

def get_intents(user_text):
    intents = {
        "banking": ["bank", "account", "deposit"],
        "financial": ["finance", "money", "cost"],
        "service": ["service", "support", "help"],
        "general": ["question", "query", "info"],
        "emotional": ["emotion", "FEeling", "satisfaction"]
    }
    
    possible_intents = []
    
    try:
        nlp = en_core_web_sm.load()
        tokens = word_tokenize(user_text)
        tokens_with_ngrams = [list(ngram) for ngram in ngrams(tokens, 2)]
        
        for token in tokens + tokens_with_ngrams:
            token_str = str(token[0])
            pos = pos_tag([token_str])[0][1]
            
            if token_str.lower() in intents.keys():
                possible_intents.extend(intents[token_str.lower()])
                
        unique_intents = list(set(possible_intents))
        
    except Exception as e:
        return ["Unknown Intent"]
    
    return unique_intents