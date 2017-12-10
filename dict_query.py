import requests
from string import ascii_lowercase as alphabet
from bs4 import BeautifulSoup as Soup
from bs4 import NavigableString
import os



def query_oxford(word, app_id, app_key, category=None):
    """
    :param word: the word to look up in the dictionary
    :param category: noun, verb, adjective, etc.
    :param app_id: oxford api id
    :param app_key: oxford api key
    :return: a tuple, (data: JSON, result_code: int)
    :result_codes: 0 - fail; 1 - success; 2 - original word not found, provides definitions for the closest match
    """
    word_in_url_format = '%20'.join(word.lower().strip().split(' '))
    lexicalCategory = ''
    if category:
        lexicalCategory = ';lexicalCategory={}'.format(category)
    url = 'https://od-api.oxforddictionaries.com/api/v1/entries/en/{}/definitions{}'.format(word_in_url_format, lexicalCategory)
    r = requests.get(url, headers = {'app_id': app_id, 'app_key': app_key})
    if  r.status_code == 200:
        data = r.json()
        result_code = 1
        return data, result_code
    elif r.status_code == 404:
        url_s = 'https://od-api.oxforddictionaries.com/api/v1/search/en?q={}&prefix=false'.format(word_in_url_format)
        r_search = requests.get(url_s, headers = {'app_id': app_id, 'app_key': app_key})
        if r_search.status_code == 200:
            word_new = r_search.json()['results'][0]['word']
            word_new_in_url_format = '%20'.join(word_new.lower().strip().split(' '))
            url_new = 'https://od-api.oxforddictionaries.com/api/v1/entries/en/{}/definitions{}'.format(word_new_in_url_format, lexicalCategory)
            r_new = requests.get(url_new, headers = {'app_id': app_id, 'app_key': app_key})
            if r_new.status_code == 200:
                data = r_new.json()
                result_code = 2
                return data, result_code
    result_code = 0
    return None, result_code


def parse_oxford(data, code):
    """
    :param data: JSON, the result of the oxford API query
    :param code: API request result: 0 - fail; 1 - success; 2 - original word not found, provides definitions for the closest match
    :return: a tuple (word, url, embed_fields). The word as it's stated in the API's reply; url link to the word in \
    the oxford dictionary; a list of dictionaries to create embed fields from, the keys are 'name' and 'value'
    """
    if code == 0:
        return None
    else:
        word = data['results'][0]['word']
        url = 'https://en.oxforddictionaries.com/definition/{}'.format(word)
        embed_fields = []
        for lexicalEntry in data['results'][0]['lexicalEntries']:
            d = {}
            d['name'] = '{}, *{}*'.format(word, lexicalEntry['lexicalCategory'])
            d['value'] = ''
            for entry in lexicalEntry['entries']:
                for i, sense in enumerate(entry['senses']):
                    if sense.get('domains'):
                        domain = sense['domains'][0]
                    else:
                        domain = ''
                    definition = sense['definitions'][0]
                    d['value'] += '{}. {}{}\n'.format(i, '*'+domain+'*: ' if domain else '', definition)
            embed_fields.append(d)
        return word, url, embed_fields


def query_merriam(word, key):
    '''
    :param word: the word to search for in the dictionaries
    :return: a list of bs4.element.Tag objects in meriam xml format
    corresponding to the word's classes (adj., verb, etc)
    '''
    url = 'http://www.dictionaryapi.com/api/v1/references/collegiate/xml/'+word.lower()+'?key='+key
    r = requests.get(url)
    soup = Soup(r.text,'xml')
    # word = soup.ew.string #the word may change during the request if you have originally queried for the past tense for example, this ensures we get the right one
    cases = soup.find_all('entry')
    # regex = re.compile(word.lower()+'(?:\[\d\])')
    # cases+= soup.find_all(id=regex)
    return cases


def parse_merriam(cases):
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
        phrase+='__**'+entry.ew.text
        if entry.fl:
            phrase+='**, *'+entry.fl.text+'*__\n' #opening text. <ew> = word, <fl> = what part of speech it is
        else:
            phrase += '**__\n'

        if entry.find('def'):
            definition_full = entry.find('def') #find the <def> tag inside the entry
            definition_content = definition_full(name=['sn', 'spl', 'dt']) #filter out all the garbage from the <def> tag
            if definition_content[0].name != 'sn': phrase += '\n' #add a new line if the first item in definition doesn't imply one
            try:
                phrase += parse_tag_list(definition_content)
            except Exception as error:
                print('Caught an exception while parsing tags:\n{}'.format(error))
        else:
            try:
                definition_content = entry.cx
                phrase += parse_tag_list(definition_content)
            except Exception as error:
                print('Caught an exception while trying to parse an entry with no <def>:\n{}'.format(error))
    return phrase


def parse_tag_list(tag_list):
    phrase = ''
    for tag in tag_list:
        is_str = isinstance(tag, NavigableString)
        if is_str:
            phrase+= tag+' '
        else:
            if tag.name in ['sx','ct']:
                phrase += '`' + parse_tag_list(tag) + '` '
            elif tag.name == 'fw':
                phrase += '*' + parse_tag_list(tag) + '*'
            elif tag.name == 'vi':
                phrase += '• ' + parse_tag_list(tag)
            elif tag.name == 'd_link':
                phrase += '`' + parse_tag_list(tag) + '` '
            elif tag.name == 'un':
                phrase += ' —' + parse_tag_list(tag)
            elif tag.name == 'it':
                phrase += parse_it(tag)
            elif tag.name == 'aq':
                phrase += ' —' + parse_tag_list(tag)
            elif tag.name == 'spl':
                phrase += '*' + parse_tag_list(tag) + '*\n'
            elif tag.name == 'sn':
                phrase += parse_sn(tag)
            else:
                phrase += parse_tag_list(tag)
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


def split_message(message):
    message_list = []
    if len(message) < 2000:
        return [message]
    else:
        i = message[:2000].rfind('\n')
        message_list.append(message[:i])
        for item in split_message(message[i:]):
            message_list.append(item)
    return message_list

