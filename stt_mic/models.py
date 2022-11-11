
from vocab import redactions
from textblob import TextBlob

def sentiment(text):
    blob = TextBlob(text)
    return blob.sentiment.polarity

def redact(text):
    tokens = text.split()
    
    processedTokens = []
    for token in tokens:
        if token in redactions:
            processedTokens.append(len(token)*'*')
        else:
            processedTokens.append(token)
    
    redactedText = ' '.join(processedTokens)
    return redactedText