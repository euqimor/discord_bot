import requests
from discord.ext import commands
from discord import Embed, Colour
from string import ascii_lowercase as alphabet
from bs4 import BeautifulSoup as Soup
from bs4 import NavigableString
from time import sleep
from cogs.utils.messages import split_message


class DictionariesCog:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['miriam', 'Miriam', 'MIRIAM', 'GODDAMITMIRIAM', 'word', 'mw', 'Merriam', 'dict'])
    async def merriam(self, ctx, *, word: str):
        """Queries Merriam-Webster's Collegiate Dictionary for a word definition. Well, tries to at least..."""
        word = ' '.join(word.split())
        # try:
        query_result = self.query_merriam(word, self.bot.config["merriam_webster_key"])
        cases = query_result  # the word may have changed if you queried for the past tense for example
        # except:
        #     await ctx.send('Something went wrong during online query')
        # try:
        phrase = self.parse_merriam(cases)
        # except:
        #     await ctx.send('Something went wrong during result parsing')
        if phrase != '' and phrase is not None:
            if len(phrase) >= 2000:
                message_list = split_message(phrase)
                # for message in message_list:
                await ctx.send(message_list[0])
                await ctx.send('\_' * 20 + '\nRead more: ' + 'https://www.merriam-webster.com/dictionary/' + '%20'.join(
                    word.split(' ')))
            else:
                await ctx.send(phrase)
        else:
            message = await ctx.send('Could not find the word or something went wrong with the request')
            sleep(4)
            await message.delete()

    @commands.command()
    async def oxford(self, ctx, *, word: str):
        """Query Oxford Dictionary for a word definition."""
        word = ' '.join(word.split())
        app_id = self.bot.config["oxford_app_id"]
        app_key = self.bot.config["oxford_app_key"]
        json_data = self.query_oxford(word, app_id, app_key)
        code = json_data[1]
        if code == 0:
            message = await ctx.send('Could not find the word or something went wrong with the request')
            sleep(4)
            await message.delete()
        else:
            if code == 1:  # if API returned the definition
                parsed_data = self.parse_oxford(json_data[0])
            elif code == 2:  # if the word couldn't be found and we are being redirected to the closest match
                redirect_data = json_data[0]
                word = ' '.join(redirect_data['results'][0]['word'].split('_'))
                json_data = self.query_oxford(word, app_id, app_key)
                parsed_data = self.parse_oxford(json_data[0])
            fields = parsed_data[2]
            title = '{} | Oxford Dictionary'.format(parsed_data[0])
            e = Embed(colour=Colour.blurple(), title=title)
            e.url = parsed_data[1]
            for field in fields:
                e.add_field(name=field['name'], value=field['value'], inline=False)
            await ctx.send(embed=e)

    def query_oxford(self, word, app_id, app_key, category=None):
        """
        :param word: the word to look up in the dictionary
        :param category: noun, verb, adjective, etc.
        :param app_id: oxford api id
        :param app_key: oxford api key
        :return: a tuple, (data: JSON, result_code: int)
        :result_codes: 0 - fail; 1 - success; 2 - original word not found, provides definitions for the closest match
        """
        word_in_url_format = '%20'.join(word.lower().strip().split(' '))
        lexical_category = ''
        if category:
            lexical_category = '/lexicalCategory={}'.format(category)
        url = 'https://od-api.oxforddictionaries.com/api/v1/entries/en/{}{}'.format(word_in_url_format, lexical_category)
        r = requests.get(url, headers={'app_id': app_id, 'app_key': app_key})
        if r.status_code == 200:
            data = r.json()
            result_code = 1
            return data, result_code
        elif r.status_code == 404:
            url_s = 'https://od-api.oxforddictionaries.com/api/v1/search/en?q={}&prefix=false'.format(
                word_in_url_format)
            r_search = requests.get(url_s, headers={'app_id': app_id, 'app_key': app_key})
            if r_search.status_code == 200 and r_search.json()['results']:
                word_new = r_search.json()['results'][0]['id']
                word_new_in_url_format = '%20'.join(word_new.lower().strip().split(' '))
                url_new = 'https://od-api.oxforddictionaries.com/api/v1/entries/en/{}/definitions{}'.format(
                    word_new_in_url_format, lexical_category)
                r_new = requests.get(url_new, headers={'app_id': app_id, 'app_key': app_key})
                if r_new.status_code == 200:
                    data = r_new.json()
                    result_code = 2
                    return data, result_code
        result_code = 0
        return None, result_code

    def parse_oxford(self, data):
        """
        :param data: JSON, the result of the oxford API query
        :return: a tuple (word, url, embed_fields). The word as it's stated in the API's reply; url link to the word in \
        the oxford dictionary; a list of dictionaries to create embed fields from, the keys are 'name' and 'value'
        """
        word = data['results'][0]['word'].capitalize()
        url = 'https://en.oxforddictionaries.com/definition/{}'.format('%20'.join(word.lower().strip().split(' ')))
        embed_fields = []
        for lexicalEntry in data['results'][0]['lexicalEntries']:
            i = 1
            d = dict()
            d['name'] = '{}, *{}*'.format(word, lexicalEntry['lexicalCategory'].lower())
            d['value'] = ''
            for entry in lexicalEntry['entries']:
                for sense in entry['senses']:
                    if sense.get('definitions'):
                        if sense.get('domains'):
                            domain = sense['domains'][0]
                        else:
                            domain = ''
                        definition = sense['definitions'][0]
                        d['value'] += '{}. {}{}\n'.format(i, '*' + domain + '*: ' if domain else '', definition)
                    elif sense.get('crossReferenceMarkers'):
                        d['value'] += '{}. {}\n'.format(i, sense['crossReferenceMarkers'][0])
                    i += 1
            embed_fields.append(d)
        return word, url, embed_fields

    def query_merriam(self, word, key):
        """
        :param word: the word to search for in the dictionaries
        :param key: merriam api key
        :return: a list of bs4.element.Tag objects in meriam xml format
        corresponding to the word's classes (adj., verb, etc)
        """
        url = 'http://www.dictionaryapi.com/api/v1/references/collegiate/xml/' + word.lower() + '?key=' + key
        r = requests.get(url)
        soup = Soup(r.text, 'xml')
        # word = soup.ew.string #the word may change during the request if you have originally queried for the past tense for example, this ensures we get the right one
        cases = soup.find_all('entry')
        # regex = re.compile(word.lower()+'(?:\[\d\])')
        # cases+= soup.find_all(id=regex)
        return cases

    def parse_merriam(self, cases):
        """
        :param cases: a list of bs4.element.Tag objects in meriam xml format
        corresponding to the word's classes (adj., verb, etc)
        :return: a formatted string with the word's meanings
        """
        phrase = ''
        i = 0
        for entry in cases:
            if i > 0:
                phrase += '\n\n'  # using counter to add new lines before every entry except the 1st one
            i += 1
            phrase += '__**' + entry.ew.text
            if entry.fl:
                phrase += '**, *' + entry.fl.text + '*__\n'  # opening text. <ew> = word, <fl> = what part of speech it is
            else:
                phrase += '**__\n'

            if entry.find('def'):
                definition_full = entry.find('def')  # find the <def> tag inside the entry
                definition_content = definition_full(
                    name=['sn', 'spl', 'dt'])  # filter out all the garbage from the <def> tag
                if definition_content[0].name != 'sn':
                    phrase += '\n'  # add a new line if the first item in definition doesn't imply one
                try:
                    phrase += self.parse_tag_list(definition_content)
                except Exception as error:
                    print('Caught an exception while parsing tags:\n{}'.format(error))
            else:
                try:
                    definition_content = entry.cx
                    phrase += self.parse_tag_list(definition_content)
                except Exception as error:
                    print('Caught an exception while trying to parse an entry with no <def>:\n{}'.format(error))
        return phrase

    def parse_tag_list(self, tag_list):
        phrase = ''
        for tag in tag_list:
            is_str = isinstance(tag, NavigableString)
            if is_str:
                phrase += tag + ' '
            else:
                if tag.name in ['sx', 'ct']:
                    phrase += '`' + self.parse_tag_list(tag) + '` '
                elif tag.name == 'fw':
                    phrase += '*' + self.parse_tag_list(tag) + '*'
                elif tag.name == 'vi':
                    phrase += '• ' + self.parse_tag_list(tag)
                elif tag.name == 'd_link':
                    phrase += '`' + self.parse_tag_list(tag) + '` '
                elif tag.name == 'un':
                    phrase += ' —' + self.parse_tag_list(tag)
                elif tag.name == 'it':
                    phrase += self.parse_it(tag)
                elif tag.name == 'aq':
                    phrase += ' —' + self.parse_tag_list(tag)
                elif tag.name == 'spl':
                    phrase += '*' + self.parse_tag_list(tag) + '*\n'
                elif tag.name == 'sn':
                    phrase += self.parse_sn(tag)
                else:
                    phrase += self.parse_tag_list(tag)
        return phrase

    def parse_sn(self, sn):
        phrase = ''
        if not sn.next.name:  # if there's no other tag (namely <snm>) inside the <sn> tag
            if sn.text[0] in alphabet:  # if <sn> content starts with a letter create an indentation on new line
                phrase += '\n   ' + sn.text + ' '
            else:  # otherwise write in the beginning of the new line
                phrase += '\n' + sn.text + ' '
        else:  # if there's a tag inside the <sn> tag, continue writing on the same line
            phrase += sn.text + ' '
        return phrase

    def parse_it(self, it):
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


def setup(bot):
    bot.add_cog(DictionariesCog(bot))
