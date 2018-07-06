# This is a dice rolling cog for a Discord bot. It supports all basic mathematical operations:
# addition, subtraction, multiplication, division, and parentheses. It also includes support for
# dice rolls. E.g. "1d20+6"
# Author: ryanalexanderhughes@gmail.com
# Based on: https://ruslanspivak.com/lsbasi-part1/ by Ryslan Spivak

from discord.ext import commands
from random import randint

# TOKEN ENUM
# Note: could use a class or enum library but this is dead simple.
TK_INT = "INT"
TK_PLUS = "PLUS"
TK_EOF = "EOF"
TK_MINUS = "MINUS"
TK_MULTIPLY = "MULTIPLY"
TK_DIVIDE = "DIVIDE"
TK_PAREN_LEFT = "PAREN_LEFT"
TK_PAREN_RIGHT = "PAREN_RIGHT"
TK_DICE = "DICE"

# Rolls dice with a given number of sides and returns the sum
def roll_dice(num_dice, num_sides):
    result = 0
    for i in range(num_dice):
        result += randint(1, num_sides)
    return result

# The lexer will create tokens from substrings to feed to
# the interpreter.
class Token():
    def __init__(self, token_type, value):
        self.type = token_type
        self.value = value
    def __str__(self):
        return "Token({token_type}, {value})".format(
            token_type = self.type,
            value = self.value
        )

class Lexer():
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.current_character = self.text[self.pos]
        self.fancy_string = ""

    def error(self):
        raise Exception("Lexer error.")

    # Advances the lexer to the next character
    def advance(self):
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_character = None
        else:
            self.current_character = self.text[self.pos]

    def skip_whitespace(self):
        while self.current_character is not None and self.current_character.isspace():
            self.advance()

    # Determines whether a substring is suitable for either an integer or a dice token
    def integer_or_dice(self):
        result = ""
        is_dice = False
        num_dice = 0
        num_sides = 0
        while self.current_character is not None:
            if self.current_character.isdigit():
                result += self.current_character
            elif self.current_character in ("d", "D"):
                if not is_dice:
                    is_dice = True
                    num_dice = int(result)
                    result = ""
                else:
                    self.error()
            else:
                break
            self.advance()
        if is_dice:
            num_sides = int(result)
            roll = roll_dice(num_dice, num_sides)
            return Token(TK_DICE, (num_dice, num_sides, roll))
        else:
            return Token(TK_INT, int(result))

    # This is used for outputting the dice rolls with some flair
    def append_fancy_string(self, string):
        self.fancy_string += str(string)

    # Grabs the next token in the string. This acts greedily and will try to
    # match the largest substring where possible (e.g. ints)
    def get_next_token(self):
        while self.current_character is not None:
            # print("Current character: " + str(self.current_character))
            if self.current_character.isspace():
                self.skip_whitespace()
                continue
            if self.current_character.isdigit():
                token = self.integer_or_dice()
                if token.type == TK_INT:
                    self.append_fancy_string(token.value)
                elif token.type == TK_DICE:
                    self.append_fancy_string("[{}]".format(token.value[2]))
                return token
            if self.current_character == "+":
                self.append_fancy_string("+")
                self.advance()
                return Token(TK_PLUS, "+")
            if self.current_character == "-":
                self.append_fancy_string("-")
                self.advance()
                return Token(TK_MINUS, "-")
            if self.current_character == "*":
                self.append_fancy_string("*")
                self.advance()
                return Token(TK_MULTIPLY, "*")
            if self.current_character == "/":
                self.append_fancy_string("/")
                self.advance()
                return Token(TK_DIVIDE, "/")
            if self.current_character == "(":
                self.append_fancy_string("(")
                self.advance()
                return Token(TK_PAREN_LEFT, "(")
            if self.current_character == ")":
                self.append_fancy_string(")")
                self.advance()
                return Token(TK_PAREN_RIGHT, ")")
            self.error()
        return Token(TK_EOF, None)

# The interpreter relies on a lexer to convert a string into tokens, then evaluates 
# those tokens to return a result. If the token list is ungrammatical, an exception will 
# be thrown.
class Interpreter():
    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()

    def error(self):
        raise Exception("Invalid syntax.")

    # Consumes a token of a given type, advancing the lexer
    def eat(self, token_type):
        if self.current_token.type == token_type:
            #print(self.current_token)
            self.current_token = self.lexer.get_next_token()
        else:
            print("ERROR: {}".format(self.current_token.type))
            self.error()

    def parse(self):
        return self.expr()

    # Evaluates an expression
    def expr(self):
        result = self.term()
        # Handles addition and subtraction tokens
        while self.current_token.type in (TK_PLUS, TK_MINUS):
            if self.current_token.type == TK_PLUS:
                self.eat(TK_PLUS)
                result += self.term()
            elif self.current_token.type == TK_MINUS:
                self.eat(TK_MINUS)
                result -= self.term()
        return result

    def term(self):
        result = self.factor()
        # Handles multiplication and division tokens
        while self.current_token.type in (TK_MULTIPLY, TK_DIVIDE):
            if self.current_token.type == TK_MULTIPLY:
                self.eat(TK_MULTIPLY)
                result *= self.factor()
            elif self.current_token.type == TK_DIVIDE:
                self.eat(TK_DIVIDE)
                result /= self.factor()
        return result

    def factor(self):
        # Handles parenthesis, int, and dice tokens
        if self.current_token.type == TK_PAREN_LEFT:
            self.paren_left()
            result = self.expr()
            self.paren_right()
        elif self.current_token.type == TK_INT:
            result = self.current_token.value
            self.eat(TK_INT)
        elif self.current_token.type == TK_DICE:
            result = self.current_token.value[2]
            self.eat(TK_DICE)
        return result

    def paren_left(self):
        self.eat(TK_PAREN_LEFT)

    def paren_right(self):
        self.eat(TK_PAREN_RIGHT)

class DiceCog:
    def __init__(self, bot):
        self.bot = bot

    # Instructs the bot to roll dice according to formatted strings.
    # E.g. roll 1d20 + 3
    # The result is sent as a message in response to the command.
    @commands.command()
    async def roll(self, context, *args):
        roll_string = "".join(args)
        lexer = Lexer(roll_string)
        interpreter = Interpreter(lexer)
        result = interpreter.parse()
        await context.send(":game_die: Rolling: {}\nResult: {}".format(lexer.fancy_string, result))

    # This is just a test command to see if the cog is working.
    @commands.command()
    async def dice_test(self, ctx):
        print("Dice test!")

    # Uses the 4d6 drop the lowest method to generate a stat array for a Dungeons and Dragons 5e character
    @commands.command()
    async def roll_stats(self, context):
        stat_rolls = []
        NUM_STATS = 6
        DICE_PER_STAT = 4
        DICE_SIDES = 6
        for i in range(NUM_STATS):
            rolls = []
            for j in range(DICE_PER_STAT):
                rolls.append(roll_dice(1, DICE_SIDES))
            rolls.remove(min(rolls))
            stat_rolls.append(sum(rolls))
        await context.send(
            ":game_die: Rolling stats!\nResult: {}, {}, {}, {}, {}, {}".format(*stat_rolls)
        )

def setup(bot):
    bot.add_cog(DiceCog(bot))
