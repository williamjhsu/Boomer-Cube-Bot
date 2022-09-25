import asyncio
import random
import discord
import imagemanipulator
import math

#Constants
reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '0️⃣', '🇦', '🇧','🇨','🇩','🇪']

#Starting with a list that will hold pick data
pickdata = [['Name', 'Pick', 'User', 'Cube']]

#Stores their pool of picked cards and discord user. Store within drafts.
class Player:

    def hasPicked(self):
        pack_nums = self.draft.pack_numbers()
        # print(pack_nums)
        return not (len(self.pack) + self.draft.currentPick == pack_nums[self.draft.currentPack-1]+1)

    def pick(self, cardIndex):
        #Checking if the card is in the pack.
        if cardIndex <= (len(self.pack) - 1):
            #Making sure they havent already picked
            if not self.hasPicked():
                asyncio.create_task(self.user.send('You have picked ' + self.pack[cardIndex].name + '.'))
                self.pool.append(self.pack[cardIndex])
                
                temppickdata = []
                tempcardname = str(self.pack[cardIndex].name) #Adding the card name to the temppickdata vector to append to file

                self.pack.pop(cardIndex)
                self.draft.checkPacks()

                tempcardname = tempcardname.replace(',', " ") #Removing commas for CSV purposes
                temppickdata.append(tempcardname)
                temppickdata.append(len(self.pack)) #Adding pick #
                temppickdata.append(self.user) #Adding the person who picked
                temppickdata.append('x') #Noting which cube was used. Will add once I get this working
                pickdata.append(temppickdata)
                

    def __init__(self, user, draft):
        self.draft = draft
        self.pack = None
        self.pool = []
        self.missedpicks = 0
        self.user = user
    
    def __repr__(self):
        return self.user

class Timer:

    async def start(self):
        #Scales the length of the timer to the size of the pack.
        #Mathematica:
        #In: NSolve[{a*Log[10, b*5] == 150, a*Log[10, b*19] == 30}, {a, b}]
        #Out: {{a -> -206.974, b -> 0.0376965}}
        #Pick + 4
        new_length = -206.974 * math.log10(0.0376965 * (self.draft.currentPick + 4))
        self.length = round(new_length)
        #A little bit of psych here. Tell them there is shorter left to pick than there really is.
        await asyncio.sleep(self.length - 12)
        #Return if this thread is now a outdated and no longer needed timer.
        if self != self.draft.timer:
            return
        # for player in self.draft.players:
        #     if not player.hasPicked():
        #         asyncio.create_task(player.user.send('Hurry! Only ten seconds left to pick!'))
        # await asyncio.sleep(12)
        if self != self.draft.timer:
            return
        # players = [player for player in self.draft.players if not player.hasPicked()]
        # for player in players:
        #     if not player.hasPicked() and self == self.draft.timer:
        #         player.missedpicks = player.missedpicks + 1
        #         if player.missedpicks == 2:
        #             asyncio.create_task(player.user.send('Ran out of time. WARNING! IF YOU MISS ONE MORE PICK YOU WILL BE KICKED FROM THE DRAFT! WARNING! IF YOU MISS ONE MORE PICK YOU WILL BE KICKED FROM THE DRAFT! WARNING! IF YOU MISS ONE MORE PICK YOU WILL BE KICKED FROM THE DRAFT! https://tenor.com/view/wandavision-wanda-this-will-be-warning-gif-20683220'))
        #         if player.missedpicks == 3:
        #             asyncio.create_task(player.user.send('Ran out of time. You have been kicked for missing 3 picks. Three strikes! you\'re out! https://tenor.com/view/strike-ponche-bateador-strike-out-swing-gif-15388719'))
        #             self.draft.kick(player)
        #
        #
        #         else:
        #             asyncio.create_task(player.user.send('Ran out of time. You have automatically picked the first card in the pack. Please pay attention to avoid wasting time!'))
        #             player.pick(0)

    def __init__(self, draft, length=150):
        self.length = length
        self.draft = draft
        asyncio.create_task(self.start())

class Draft:
    #cube: The cube the pool was created from
    #pool: The cards remaining to be picked from
    #players: The players in the draft. Player class.
    #channel: The channel the draft was started from
    #timer: The timer tracking the picks. Reassign every pick.
    def __init__(self, cube, channel):
        self.cube = cube[:]
        self.pool = cube[:]
        self.players = [] #Was orginally a default value. Created very complicated errors with underlying objects and references in the Python interpter. Wasn't being used at the time anyway.
        self.channel = channel
        self.timer = None
        self.currentPick = -1
        self.currentPack = 0

    def newPacks(self):
        """
        need to edit to distribute number of cards per pack based on how many players
        :return:
        """
        self.currentPick = 1
        self.currentPack += 1
        self.timer = Timer(self) #resets the timer
        self.players.reverse()

        pack_nums = self.pack_numbers()
        FullList = random.sample(self.pool, len(self.players) * int(pack_nums[self.currentPack-1]))
        # adjusts to number of players
        self.pool = [q for q in self.pool if q not in FullList] #Removes the cards from the full card list

        i = 0 #For pulling cards from the full list into packs
        for player in self.players:
            pack = sortPack(FullList[i:i+int(pack_nums[self.currentPack-1])])
            player.pack = pack #Holds the packs
            i = i+int(pack_nums[self.currentPack-1])
            #splices reactions into pack
            packWithReactions = self._helper_cardnames(player.pack)
            asyncio.create_task(send_pack_message("Here's your #" + str(self.currentPack) + " pack! React to select a card\n"+str(packWithReactions), player, pack))

    def pack_numbers(self):
        """
        1000/player_num = number of cards per person
        if number of cards is not whole number:
            cut to nearest whole number
            take leftover cards, and randomly give them to players
                write message at end saying "you received an extra card(s)"

        :param
        :return: array of cards per pack in order
        """
        player_num = len(self.players)
        leftover_cards = len(self.cube) % player_num
        if leftover_cards != 0:  # if 1000/number of players isn't a whole number
            rounded_num = math.floor(len(self.cube)/player_num)
            """
            take leftover cards and figure out where to randomly distribute them
            call leftover_distribution()
            not actually here but call it when the last draft is done from split_packs and take all leftover cards
            """
        else:
            rounded_num = len(self.cube)/player_num

        return self.split_packs(rounded_num)

    def split_packs(self, rounded):
        """
        split packs in half, round up and down if necessary
        return list of number of cards per pack in order <= 20 each
        :param rounded:
        :return: list
        """
        if rounded <= 20:  # if the list is already <= 20, then no splitting
            return [rounded]

        splitting = 1
        cards_per_pack = []
        copy_list = []
        rounded /= 2
        cards_per_pack.append(math.ceil(rounded))
        cards_per_pack.append(math.floor(rounded))

        if rounded <= 20:  # if the list is already <= 20, then no splitting
            return [rounded]

        while splitting:
            for a in cards_per_pack:
                copy_list.append(math.ceil(a/2))
                copy_list.append(math.floor(a/2))
            cards_per_pack = copy_list
            if cards_per_pack[0] <= 20:  # first element will always be the highest number
                splitting = 0

        return cards_per_pack

    def leftover_distribution(self):
        """
        take number of leftover cards
        pull them from the cardpool and then somewhat evenly distribute them at the end
        :param self:
        :param
        :return:
        """
        player_id = 0
        cards_to_players = []
        for x in self.players:  # make list of lists with number of players
            cards_to_players.append([])

        gifted_cards = []
        for a in self.pool:  # only called when JUST the leftover cards are left in the pool
            if player_id > len(self.players) - 1:  # wrap around if still more cards
                player_id = 0
            cards_to_players[player_id].append(a)
            player_id += 1

        player_id = 0
        for y in self.players:  # send message of leftover cards to players
            asyncio.create_task(gift_leftovers(cards_to_players[player_id], self.players[player_id]))
            player_id += 1

    def rotatePacks(self):
        self.currentPick += 1
        self.timer = Timer(self) #resets the timer

        #Creates a list of all the packs
        packs = [player.pack for player in self.players]
        for player in self.players:
            #Gives the player the next pack in the list. If that would be out of bounds give them the first pack.
            player.pack = packs[0] if (packs.index(player.pack) + 1) >= len(packs) else packs[packs.index(player.pack) + 1]
            #splices reactions into pack
            packWithReactions = self._helper_cardnames(player.pack)
            asyncio.create_task(send_pack_message('Your next pack: \n'+str(packWithReactions), player, player.pack))

    def _helper_cardnames(self,pack):
        """
        function to get card names
        :return: str
        """
        pack_str = ''
        for a, b in zip(reactions, pack):
            pack_str += f'{a} :  [{b.name}] (<https://yugioh.fandom.com/wiki/{b.name.replace(" ", "_")}>)\n'
        return pack_str

        #Decides if its time to rotate or send a new pack yet.

    def checkPacks(self):
        #Checks if every player has picked.
        pack_nums = self.pack_numbers()
        if len([player for player in self.players if not player.hasPicked()]) == 0:
            if self.currentPick < int(pack_nums[self.currentPack - 1]):
                self.rotatePacks()
            elif self.currentPack >= len(self.pack_numbers()):
                for player in self.players:
                    asyncio.create_task(player.user.send('The draft is now finished. Use !ydk or !mypool to get started on deckbuilding.'))
            else:
                self.newPacks()
    
    def startDraft(self):
        self.newPacks()

    def kick(self, player):
        #A little worried about how we currently call this from the seperate timer thread from all the other main logic.
        #Drops the players pack into the void currently. 
        self.players.remove(player)
        self.checkPacks()
        asyncio.create_task(self.channel.send("A player has been kicked from the draft"))

def sortPack(pack):
    monsters = [card for card in pack if 'monster' in card.cardType.lower() and ('synchro' not in card.cardType.lower() and 'xyz' not in card.cardType.lower())]
    spells = [card for card in pack if 'spell' in card.cardType.lower()]
    traps = [card for card in pack if 'trap' in card.cardType.lower()]
    extras = [card for card in pack if 'xyz' in card.cardType.lower() or 'synchro' in card.cardType.lower()]
    return monsters + spells + traps + extras

async def add_reactions(message, emojis):
    for emoji in emojis:
        asyncio.create_task(message.add_reaction(emoji))

#This exists to allow making the pack messages async.
async def send_pack_message(text, player, pack):
    asyncio.create_task(add_reactions(await player.user.send(content=text, file=discord.File(fp=imagemanipulator.create_pack_image(pack),filename="image.jpg")), reactions[:len(pack)]))

#send players message about gifted leftover cards
async def gift_leftovers(cards, player):
    asyncio.create_task(player.user.send('These are your gifted cards: ') + str(cards))
