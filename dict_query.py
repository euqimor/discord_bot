import requests
import re
from string import ascii_lowercase as alphabet
from bs4 import BeautifulSoup as Soup

def query_merriam(word):
    '''
    :param word: the word to search for in the dictionaries
    :return: a list of bs4.element.Tag objects in meriam xml format
    corresponding to the word's classes (adj., verb, etc)
    '''
    key = '1cbb9d6b-e0d5-4822-968d-d16f4942ab65'
    url = 'http://www.dictionaryapi.com/api/v1/references/collegiate/xml/'+word.lower()+'?key='+key
    r = requests.get(url)
    soup = Soup(r.text,'xml')
    regex = re.compile(word.lower()'(?:\[\d\])*$')
    cases = soup.find_all(id=regex)
    return cases

def compose_merriam(cases, word):
    '''
    :param cases: a list of bs4.element.Tag objects in meriam xml format
    corresponding to the word's classes (adj., verb, etc)
    :return: a formatted string with the word's meanings
    '''
    phrase = ''
    i=0
    for item in cases:
        y=0
        i+=1
        phrase+='**'+word.lower()', '+item.find('fl').text+'**\n'
        phrase+='**'+str(i)+'**\n'
        for definition in item.find_all('dt'):
            phrase+='	'+alphabet[y]+' '
            y+=1
            if definition.sx is not None:
                phrase+=definition.next+definition.sx.text+'\n'
            else:
                phrase+=definition.next+'\n'
        phrase+='\n'
    return phrase
