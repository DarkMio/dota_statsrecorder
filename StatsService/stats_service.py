import simplejson
import requests
import log
import logging
from mysql import database
from ConfigParser import ConfigParser

logger = logging.getLogger('root')


class SteamAPI(object):

    def __init__(self):
        # setup config parser
        config = ConfigParser()
        config.read('config.ini')

        # get the steamkey
        self.key = config.get('STEAM', 'key')
        # build up a dictionary with all heroes
        self.hero_dict = self.build_heroes()

        self.db = database()

    """"Generates a dictionary with all heroes so far."""
    def build_heroes(self):
        carebox = {}  # throwaway just to return it
        for i in range(50):
            req_param = {'key': self.key,
                         'format': 'json',
                         'language': 'en',
                         'itemizedonly': 'false'}
            hero_data = []
            try:
                request = requests.get('https://api.steampowered.com/IEconDOTA2_570/GetHeroes/v1/', params=req_param)
                hero_data = simplejson.loads(request.text, encoding="utf-8")
            except:
                pass

            if 'result' in hero_data:
                for result in hero_data['result']['heroes']:
                    # convert it to string > should < always be ascii.
                    hero_name = str(result['localized_name'])
                    hero_id = result['id']
                    # make a dict.
                    carebox[hero_id] = hero_name

                break
            if i == 49:
                raise IOError("SteamAPI didn't respond after 50 retries.")

        return carebox

    def get_history(self, steamID):
        return

    def get_history_old(self, steamID, heroID=None, last_mID=None, last_checked=None, first_instance=True):
        """Builds up a complete history, gets the latest matches and does everything
            we need it for anyway."""
        # heroID can have different types of data.
        # None -> Get history from -> to
        # True -> Unfold the dict and query all matches with hero
        # INTEGER -> Get history from one particular hero

        last_checked = self.db.get_last_checked(steamID)

        if first_instance and not last_checked:
            logger.info('Building up a database with all matches from SteamID {0}.'.format(steamID))
            for hero_id in self.hero_dict:
                logger.info('Getting all matches with Hero {1} for SteamID {0}.'.format(steamID, self.hero_dict[hero_id]))
                self.get_history(steamID, heroID=hero_id, first_instance=False)
            return

        elif first_instance and last_checked:
            logger.info('Getting recent match-history of SteamID {0}.'.format(steamID))
            last_checked = self.db.get_last_checked(steamID)
            self.get_history(steamID, last_checked=last_checked, heroID=0, first_instance=False)
            return

        for i in range(50):
            logger.info('Acquiring the history of SteamID {0}.'.format(steamID))
            req_param = {'key': self.key, 'format': 'json', 'account_id': steamID, 'hero_id': heroID, 'start_at_match_id': last_mID}
            match_history = []
            try:
                request = requests.get('https://api.steampowered.com/IDOTA2Match_570/GetMatchHistory/v1/', params = req_param)
                match_history = simplejson.loads(request.text, encoding = "utf-8")
            except:
                pass
            if 'result' in match_history:
                i = True
                if match_history['result']['status'] == 1:
                    for match in match_history['result']['matches']:
                        if match['match_id'] == last_checked:
                            logger.info('Built up the todolist with the most recent games.')
                            i = None
                            break
                        else:    
                            self.db.todolist_match(steamID, match['match_id'])

                    if match_history['result']['results_remaining'] > 0 and i:
                        logger.info('There are still games history-games to fetch.')
                        self.get_history(steamID,
                                         heroID=heroID,
                                         last_mID=match_history['result']['matches'][-1]['match_id'],
                                         last_checked=last_checked,
                                         first_instance=False)
                break
            if i == 49:
                raise IOError("SteamAPI didn't respond after 50 retries.")
            
    """Deprecated for now."""
    def records_service(self, steamID):
        """Takes care about matches and records"""

        steamID = int(steamID)
        empty = False
        while empty != True: # redo and redo and redo that shit until the database is empty for one steamID

            matchID = self.db.return_todolist(steamID)
            if not matchID:
                empty = True
                logger.info("Successfully loaded all matches for SteamID {0}.".format(steamID))
                return
            else:
                for match_ID in matchID:
                    match_ID = match_ID[0]
                    logger.info('Acquiring Match Data for MatchID {0}.'.format(match_ID))
                    req_param = {'key': self.key, 'format': 'json', 'match_id': match_ID}
                    match = []
                    try:
                        request = requests.get('https://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/v1/', params = req_param)
                        match = simplejson.loads(request.text, encoding = "utf-8")
                    except:
                        pass


                    i = True # this is just for spam protection in the logger
                    
                    if 'result' in match:
                        match = match['result']
                        abandon = False
                        bot_list = [3, 4]
                        ignore_list = [19, 15, 10, 9, 7, 6]



                        if match['lobby_type'] in bot_list:
                            logger.info("MatchID {0} is a botgame - ignoring match!".format(match_ID))
                            self.db.delete_entry_in_todolist(steamID, match_ID)
                        

                        elif match['game_mode'] in ignore_list:
                            logger.info("MatchID {0} is a fun-gamemode - ignoring match!".format(match_ID))
                            self.db.delete_entry_in_todolist(steamID, match_ID)

                        else:    
                            
                            #team = hero_id = victory = no_tower = gpm = max_gold = None
                            #xpm = None
                            for player in match['players']:
                                if "leaver_status" in player and i: 
                                    if player['leaver_status'] != 0:
                                        i = None
                                        abandon = True
                                        logger.info("MatchID {0} is abandoned!".format(match_ID))

                                #elif i:
                                #    i = None
                                #    logger.info('MatchID {0} is a bot-game!'.format(match_ID))
                                #    abandon = True #it's a botgame, nobody counts botgames.

                                #if "account_id" in player:
                                if player['account_id'] == steamID:

                                    # assign a team
                                    if (player["player_slot"] >> 7 ) == 1:
                                        team = 'dire'
                                    else:
                                        team = 'radiant'

                                    hero_id = player['hero_id']


                                    if (match['radiant_win'] == True and team == 'radiant'
                                        or match['radiant_win'] == False and team == 'dire'):
                                        victory = True
                                    else:
                                        victory = False

                                    if (match['tower_status_radiant'] == 2047 and team == 'radiant'
                                        or match['tower_status_dire'] == 2047 and team == 'dire'):
                                        no_tower = True
                                    else:
                                        no_tower = False

                                    gpm = player['gold_per_min']
                                    max_gold = player['gold_per_min'] * (match['duration']/60)
                                    xpm = player['xp_per_min']
                                    max_xp = player['xp_per_min'] * (match['duration']/60)
                                    lh = player['last_hits']
                                    denies = player['denies']
                                    kills = player['kills']
                                    deaths = player['deaths']
                                    assist = player['assists']
                                    # (K+A)/D - D is 1 when D == 0
                                    kda_death = (player['deaths'] == 0 and 1) or player['deaths']
                                    kda = ((float(player['kills']) + player['assists']) / kda_death)
                                    hDMG = player['hero_damage']
                                    tDMG = player['tower_damage']
                                    hHEAL = player['hero_healing']
                                    l25_time = None

                                    try:
                                        for levelup in player['ability_upgrades']:
                                            if levelup['level'] == 25:
                                                l25_time = levelup['time']
                                    except KeyError:
                                        pass

                            fblood_time = match['first_blood_time']
                            total_time = match['duration']
                            
                            # just to have everything together.
                            data_collect = {
                                'steamID': steamID, 'matchID': match_ID, 'team': team, 'hero_id': hero_id,
                                'victory': victory, 'abandon': abandon, 'no_tower': no_tower, 'gpm': gpm,
                                'xpm': xpm, 'max_gold': max_gold, 'max_xp': max_xp, 'lh': lh, 'denies': denies,
                                'kills': kills, 'assists': assist, 'deaths': deaths, 'kda': kda, 'hDMG': hDMG,
                                'tDMG': tDMG, 'hHEAL': hHEAL,
                                'l25_time': l25_time, 'fblood_time': fblood_time, 'total_time': total_time,
                                }

                            if not abandon:
                                comp_data = self.db.return_records(steamID)

                                self.db.store_meta(steamID, last_checked=match_ID, victory=victory)
                                
                                if comp_data:
                                    for column in comp_data:
                                        spamprotect = True
                                        # record comparison comes here
                                        record = column[1]


                                        # this needs special handling
                                        if record == 'no_tower':
                                            if no_tower == True:
                                                self.db.store_records(rec_type='no_tower', **data_collect)

                                        if record == 'highest_gpm':
                                            if gpm > column[7]:
                                                self.db.store_records(rec_type='highest_gpm', **data_collect)

                                        if record == 'highest_xpm':
                                            if xpm > column[8]:
                                                self.db.store_records(rec_type='highest_xpm', **data_collect)

                                        if record == 'most_gold':
                                            if max_gold > column[9]:
                                                self.db.store_records(rec_type='most_gold', **data_collect)

                                        if record == 'most_xp':
                                            if max_xp > column[10]:
                                                self.db.store_records(rec_type='most_xp', **data_collect)

                                        if record == 'most_lh':
                                            if lh > column[11]:
                                                self.db.store_records(rec_type='most_lh', **data_collect)

                                        if record == 'most_denies':
                                            if denies > column[12]:
                                                self.db.store_records(rec_type='most_denies', **data_collect)

                                        if record == 'most_kills':
                                            if kills > column[13]:
                                                self.db.store_records(rec_type='most_kills', **data_collect)

                                        if record == 'most_assists':
                                            if assist > column[14]:
                                                self.db.store_records(rec_type='most_assists', **data_collect)

                                        if record == 'most_deaths':
                                            if deaths > column[15]:
                                                self.db.store_records(rec_type='most_deaths', **data_collect)

                                        # needs special handling
                                        if record == 'no_deaths':
                                            if deaths == 0:
                                                self.db.store_records(rec_type='no_deaths', **data_collect)

                                        if record == 'best_kda':
                                            if kda > column[16]:
                                                self.db.store_records(rec_type='best_kda', **data_collect)

                                        if record == 'most_hDMG':
                                            if hDMG > column[17]:
                                                self.db.store_records(rec_type='most_hDMG', **data_collect)

                                        if record == 'most_tDMG':
                                            if tDMG > column[18]:
                                                self.db.store_records(rec_type='most_tDMG', **data_collect)

                                        if record == 'most_hHEAL':
                                            if hHEAL > column[19]:
                                                self.db.store_records(rec_type='most_hHEAL', **data_collect)

                                        if record == 'l25_time':
                                            if l25_time < column[20]:
                                                self.db.store_records(rec_type='l25_time', **data_collect)

                                        if record == 'fastest_fblood_time':
                                            if fblood_time < column[21]:
                                                self.db.store_records(rec_type='fastest_fblood_time', **data_collect)

                                        if record == 'longest_fblood_time':
                                            if fblood_time > column[21]:
                                                self.db.store_records(rec_type='longest_fblood_time', **data_collect)

                                        if record == 'fastest_total_time':
                                            if total_time < column[22]:
                                                self.db.store_records(rec_type='fastest_total_time', **data_collect)

                                        if record == 'longest_total_time':
                                            if total_time > column[22]:
                                                self.db.store_records(rec_type='longest_total_time', **data_collect)


                                else:
                                    self.db.store_records(**data_collect)

                            self.db.delete_entry_in_todolist(steamID, match_ID)

                    else:
                        logger.error("SteamAPI didn't respond, ignoring entry.")

    def get_steam_nickname(self, steamID):
        """Returns the nickname of someones SteamID. This can be fed with a vanity URL as well."""
        if isinstance(steamID, basestring):
            for i in range(50):
                req_param = {'key': self.key, 'format': 'json', 'vanityurl': steamID,}
                url_data = []
                try:
                    request = requests.get('https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/', params = req_param)
                    url_data = simplejson.loads(request.text, encoding = "utf-8")
                except:
                    pass
                if url_data['response']['success'] == 1:

                    if url_data['response']['success'] == 1:
                        steamID_64 = url_data['response']['steamid']
                    else:
                        logger.error("URL couldn't be resolved.")
                    break

                elif url_data['response']['success'] == 42:
                    logger.error('VanityURL is no real URL.')
                    break

            if i == 49:
                raise IOError("SteamAPI didn't respond after 50 retries.")
        else:
            if steamID > 76561197960265728:
                steamID_64 = steamID
                steamID_32 = steamID - 76561197960265728
            else:
                steamID_64 = steamID + 76561197960265728
                steamID_32 = steamID


        for i in range(50):
            logger.info('Downloading Steam Profile Data for SteamID {0}.'.format(steamID_64))
            req_param = {'key': self.key, 'format': 'json', 'steamids': steamID_64,}
            profile_data = []
            try:
                request = requests.get('https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/', params = req_param)
                profile_data = simplejson.loads(request.text, encoding = "utf-8")
            except:
                pass


            if profile_data['response']['players'][0]['steamid'] == steamID_64:
                nickname = profile_data['response']['players'][0]['personaname']
                break
            else:
                logger.errer('SteamID seems to produce garbage again.')
            if i == 49:
                raise IOError("SteamAPI didn't respond after 50 retries.")
        return nickname

    """Deprecated for now."""
    def data_sample(self):
        """This is a data sample with locally stored data.
            Here should be all examples of records."""

        sampledata = simplejson.load(open('sampledata.json', 'r'))
        sampledata = sampledata['result']


        abandon = False
        for player in sampledata['players']:
            if player['leaver_status'] != 0:
                abandon = True
                print "Game is abandoned!"

            if player['account_id'] == 66332433:
                if (player["player_slot"] >> 7 ) == 1:
                    team = 'dire'
                else:
                    team = 'radiant'
                print self.hero_dict[player['hero_id']], "Stats:"
                if (sampledata['radiant_win'] == True and team == 'radiant'
                    or sampledata['radiant_win'] == False and team == 'dire'):
                    print "Was victorious!"
                else:
                    print "Has lost!"

                if (sampledata['tower_status_radiant'] == 2047 and team == 'radiant'
                    or sampledata['tower_status_dire'] == 2047 and team == 'dire'):
                    print "They finished the game without loosing one single tower! Glorious!"

                print "GPM:", player['gold_per_min']
                print "Total Gold:", player['gold_per_min'] * (sampledata['duration']/60) // 1000, "k"
                print "XPM:", player['xp_per_min']
                print "Total XP:", player['xp_per_min'] * (sampledata['duration']/60) // 1000, "k"
                print "Last Hits:", player['last_hits']
                print "Denies:", player['denies']
                print "Kills:", player['kills']
                print "Deaths:", player['deaths']
                print "Assists:", player['assists']
                print "KDA:", ((float(player['kills']) + player['assists']) / player['deaths'])
                print "Hero DMG:", player['hero_damage']
                print "Tower DMG:", player['tower_damage']
                print "Hero Healing:", player['hero_healing']


                for levelup in player['ability_upgrades']:
                    if levelup['level'] == 25:
                        print "L25 in", (levelup['time'] / 60), "min"
        print "Firstblood in", sampledata['first_blood_time'] / 60, "minutes"
        print "Game Total Time:", sampledata['duration'] / 60, "minutes"
        print "Leaver status:", abandon


if __name__ == '__main__':

    logger = log.setup_custom_logger('root')
    steamID_64 = 76561198026598161
    steamID_32 = steamID_64 - 76561197960265728

    # sA = steamAPI()

    # print sA.get_steam_nickname(steamID='darkmio')

#    sA.get_history(steamID_32) # should build up a database
#    sA.records_service(steamID_32) # should process the games
#    sA.get_history(steamID_32) # should now have everything and query the latest games
#    sA.records_service(steamID_32) # should process these last games

    sA = SteamAPI()
    sA.get_history('66332433')
    sA.records_service('66332433')
