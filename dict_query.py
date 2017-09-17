import requests
import re
from string import ascii_lowercase as alphabet
from bs4 import BeautifulSoup as Soup

from bs4 import element

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
    regex = re.compile(word.lower()+'(?:\[\d\])*$')
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
        phrase+='**'+word.lower()+', '+item.find('fl').text+'**\n'
        phrase+='**'+str(i)+'**\n'
        for definition in item.find_all('dt'):
            phrase+='	'+alphabet[y]+' '
            y+=1
            if definition.next.name:
                definition_text = ':*'+definition.next.text+'* :'
            else:
                definition_text = definition.next
            if definition.sx is not None:
                phrase+=definition_text+definition.sx.text+'\n'
            else:
                phrase+=definition_text+'\n'
        phrase+='\n'
    return phrase


def parse_merriam(cases, word):
    '''
    :param cases: a list of bs4.element.Tag objects in meriam xml format
    corresponding to the word's classes (adj., verb, etc)
    :return: a formatted string with the word's meanings
    '''
    phrase = ''
    for entry in cases:
        phrase+='**'+entry.ew.text+'**, *'+entry.fl.text+'*' #opening text. <ew> = word, <fl> = what part of speech it is
        definition_full = entry.find('def') #find the <def> tag inside the entry
        definition_content = definition_full(name = ['sn','dt']) #filter out all the garbage from the <def> tag
        for tag in definition_content:
            if tag.name == 'sn':
                if not tag.next.name: #if there's no other tag (namely <snm>) inside the <sn> tag
                    if tag.text[0] in alphabet: #create an indentation on new line if <sn> content starts with a letter
                        phrase+='\n   '+tag.text+' '
                    else: #write in the beginning of the new line otherwise
                        phrase += '\n' + tag.text+' '
                else: #if there's a tag inside the <sn> tag, continue writing on the same line
                    phrase += tag.text + ' '
            elif tag.name == 'dt':
                if not tag.next.name: #if <dt>'s content doesn't start with another tag
                    sx = tag(name = 'sx') #collect all the <sx> tags for parsing
                    phrase += tag.next + ' ' #add the definition text
                    if sx != []: #if there are <sx> tags, add the first word from the tag in italic (to filter out garbage tags after the word)
                        for sx_tag in sx:
                            phrase+='*`'+sx_tag.next+'`* '
                if tag.next.name: #TODO parse the inner <dt>'s tag (should be <un>)
                    phrase += '[<UN> SOMETHING <\\UN>] '
    return phrase
