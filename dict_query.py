import requests
import re
from string import ascii_lowercase as alphabet
from bs4 import BeautifulSoup as Soup

 #TODO "b (1) : talk   discourse   • putting one's feelings into  word**s(2) :the text of a vocal musical composition"
 #TODO get rid of **; add a space after italic words; actualize the comments

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
    cases = soup(id=word)
    regex = re.compile(word.lower()+'(?:\[\d\])')
    cases+= soup.find_all(id=regex)
    return cases


def parse_merriam(cases, word):
    '''
    :param cases: a list of bs4.element.Tag objects in meriam xml format
    corresponding to the word's classes (adj., verb, etc)
    :return: a formatted string with the word's meanings
    '''
    phrase = ''
    i = 0
    for entry in cases:
        if i > 0: phrase+='\n\n' #using counter to add new lines before every entry except the 1st one
        i+=1
        phrase+='__**'+entry.ew.text+'**, *'+entry.fl.text+'*__\n' #opening text. <ew> = word, <fl> = what part of speech it is
        definition_full = entry.find('def') #find the <def> tag inside the entry
        definition_content = definition_full(name = ['sn','dt']) #filter out all the garbage from the <def> tag
        if definition_content[0].name != 'sn': phrase+='\n' #add a new line if the first item in definition doesn't imply one
        for tag in definition_content:
            if tag.name == 'sn':
                phrase+=parse_sn(tag)
            elif tag.name == 'dt':
                phrase += parse_tag(tag)
    return phrase


def parse_sn(sn):
    phrase = ''
    if not sn.next.name:  # if there's no other tag (namely <snm>) inside the <sn> tag
        if sn.text[0] in alphabet:  # if <sn> content starts with a letter create an indentation on new line
            phrase += '\n   ' + sn.text + ' '
        else:  # otherwise write in the beginning of the new line
            phrase += '\n' + sn.text + ' '
    else:  # if there's a tag inside the <sn> tag, continue writing on the same line
        phrase += sn.text + ' '
    return phrase


def parse_it(it):
    phrase = ''
    if it.previous_sibling and it.previous_sibling.name:
        previous_tag = it.previous_sibling.name
    else:
        previous_tag = False
    if it.next_sibling and it.next_sibling.name:
        next_tag = it.next_sibling.name
    else:
        next_tag = False

    if previous_tag == 'it' and next_tag == 'it':
        phrase += it.next
    elif previous_tag != 'it' and next_tag == 'it':
        phrase += '*' + it.next
    elif previous_tag == 'it' and next_tag != 'it':
        phrase += it.next + '* '
    else:
        phrase += '*' + it.next + '* '

    return phrase


def parse_tag(tag):
    phrase = ''
    for child in tag.children:
        if not child.name:
            phrase+=child
        elif child.name == 'sx':
            phrase += '`' + child.next + '` '
        elif child.name == 'fw':
            phrase += '*' + child.next + '*'
        elif child.name == 'vi':
            phrase += '• '+parse_tag(child)
        elif child.name == 'd_link':
            phrase += '`' + child.next + '` '
        elif child.name == 'un':
            phrase += parse_tag(child)
        elif child.name == 'it':
            phrase+= parse_it(child)
        elif child.name == 'aq':
            phrase += ' —*'+child.text+'*'
    return phrase
