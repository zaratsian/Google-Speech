
import requests

def getRedactions():
    r = requests.get('https://raw.githubusercontent.com/LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words/master/en')
    return [x for x in (r.text).split('\n') if x.strip()!='']

redactions = getRedactions()
