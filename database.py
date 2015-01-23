import sqlite3
import logging
import log

class database(object):

    def __init__(self):
        self.db = sqlite3.connect('match_database.db', check_same_thread=False, isolation_level=None)
        self.cur = self.db.cursor()

        self.database_init()

        # This database contains dynamic tables and one static table:
        # TABLE records: SteamID | IRC Name | Last Match | Recordstats (not designed yet)
        # TABLE (dynamic) SteamID: contains all matches ever found
        #
        # The point of dynamic generated tables is, to store a huge chunk of data in different
        # tables, which can be accessed as fast as possible. There should be approx. 2k entries
        # per dynamic table.

    def database_init(self):
        self.cur.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="records"')
        already_exists = self.cur.fetchone()
        if not already_exists:
            self.cur.execute('CREATE TABLE IF NOT EXISTS records (steamID, rec_type, matchID, team, hero_id, victory, no_tower, gpm, xpm, max_gold, max_xp, lh, denies, kills, assists, deaths, kda, hDMG, tDMG, hHEAL, l25_time, fblood_time, total_time)')
            logger.info('Database is generated and ready.')
        else:
            logger.info('Database was already generated and is ready.')

        # same stuff for the todolist-table.

        self.cur.execute('SELECT name FROM sqlite_master where type="table" and name="todolist"')
        already_exists = self.cur.fetchone()

        if not already_exists:
            self.cur.execute('CREATE TABLE IF NOT EXISTS todolist (steamID INT, matchID INT);')
            logger.info('Created db-table todolist for the SteamAPI.')

        # same stuff for the meta-table.

        self.cur.execute('SELECT name FROM sqlite_master where type="table" and name="meta"')
        already_exists = self.cur.fetchone()

        if not already_exists:
            self.cur.execute('CREATE TABLE IF NOT EXISTS meta (steamID INT, last_checked INT, wins INT, games INT, IRCname);')
            logger.info('Created meta-table for everything else we need to know.')

    def database_print(self):
        self.cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        databases = self.cur.fetchall()
        print "\n> Printing tables + first entry <"
        print "  Table     | first entry"
        print "--------------------------"
        for name in databases:
            self.cur.execute('SELECT * FROM "{0}"'.format(name[0]))
            entry = (self.cur.fetchone() == None and "empty table") or self.cur.fetchone()
            print "  "+name[0], "\t|", entry
        print ""

    def write_match(self, steamID, matchID):

        self.cur.execute('SELECT name FROM sqlite_master WHERE type="table" AND name=?;', (steamID,))
        already_exists = self.cur.fetchone()

        if not already_exists:
            self.cur.execute('CREATE TABLE "{0}" (matchID INT);'.format(steamID))    
            logger.info('Created db-table for SteamID: {}'.format(steamID))


        self.cur.execute('SELECT matchID FROM "{0}" WHERE matchID = {1}'.format(steamID, matchID))
        already_exists = self.cur.fetchone()
        if not already_exists:
            self.cur.execute('INSERT INTO "{0}" VALUES ({1});'.format(steamID, matchID))
            logger.info('Wrote matchID {1} into the database of steamID {0}.'.format(steamID, matchID))
        else:
            logger.info('MatchID {1} was already in the table of steamID {0}.'.format(steamID, matchID))



    def return_todolist(self, steamID):
        self.cur.execute('SELECT MatchID FROM todolist WHERE steamID = ? ORDER BY matchID ASC;', (steamID, ))
        matchIDs = self.cur.fetchall()

        if matchIDs:
            return matchIDs # returns tuples in lists
        else:
            return


    def todolist_steamID(self):
        self.cur.execute('SELECT steamID FROM todolist')
        steamID = self.cur.fetchone()
        if steamID:
            return steamID[0] # returns a number


    def todolist_match(self, steamID, matchID):

        self.cur.execute('INSERT INTO todolist VALUES (?, ?);', (steamID, matchID))
        logger.info('Wrote matchID {1} for steamID {0} in todolist-database.'.format(steamID, matchID))

    def sort_todolist(self):

        self.cur.execute('SELECT CAST(matchID as number) FROM todolist ORDER BY matchID ASC;')
        logger.info('Sorted the Todolist by MatchIDs.')
        data = self.cur.fetchall()
        for line in data:
            print line 

    def delete_entry_in_todolist(self, steamID, matchID):
        self.cur.execute('DELETE FROM todolist WHERE steamID = ? AND MatchID = ?', (steamID, matchID))
        self.cur.execute('SELECT * FROM todolist WHERE steamID = ? AND MatchID = ?', (steamID, matchID))
        if not self.cur.fetchall():
            logger.info('Deleted MatchID {1} from SteamID {0} in todolist'.format(steamID, matchID))



    def store_records(self, steamID, matchID, team, hero_id, victory, abandon, no_tower, gpm, xpm, max_gold, max_xp, lh,
            denies, kills, assists, deaths, kda, hDMG, tDMG, hHEAL, l25_time, fblood_time, total_time, rec_type=None):

        self.cur.execute('SELECT * FROM records where steamID = ?', (steamID,))
        init = self.cur.fetchone()
        if not init: # hopefully this will work with an empty database.
            record_list = ['no_tower', 'highest_gpm', 'highest_xpm', 'most_gold', 'most_xp', 'most_lh', 'most_denies',
                'most_kills', 'most_assists', 'most_deaths', 'no_deaths', 'best_kda', 'most_hDMG', 'most_tDMG', 'most_hHEAL', 'l25_time',
                'fastest_fblood_time', 'longest_fblood_time', 'fastest_total_time', 'longest_total_time']
            for record_types in record_list:

                self.cur.execute('INSERT INTO records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);',
                    (steamID, record_types, matchID, team, hero_id, victory, no_tower, gpm, xpm, max_gold, max_xp, lh, denies, kills, assists, deaths, kda, hDMG, tDMG, hHEAL, l25_time, fblood_time, total_time,))

            self.cur.execute('UPDATE records SET deaths = 0 WHERE steamID = ? and rec_type = "no_deaths"', (steamID,))



        logger.info('Found new record of type: {0}'.format(rec_type))
        if not rec_type == 'no_tower' and not rec_type == 'no_deaths':
            self.cur.execute('UPDATE records SET steamID=?, rec_type=?, matchID=?, team=?, hero_id=?, victory=?, no_tower=?, gpm=?, xpm=?, max_gold=?, max_xp=?, lh=?, denies=?, kills=?, assists=?, deaths=?, kda=?, hDMG=?, tDMG=?, hHEAL=?, l25_time=?, fblood_time=?, total_time=? WHERE rec_type = ? AND steamID = ?;',
                (steamID, rec_type, matchID, team, hero_id, victory, no_tower, gpm, xpm, max_gold, max_xp, lh, denies, kills, assists, deaths, kda, hDMG, tDMG, hHEAL, l25_time, fblood_time, total_time, rec_type, steamID,))

        elif rec_type == 'no_tower':
            self.cur.execute('UPDATE records SET steamID=?, matchID=?, team=?, hero_id=?, victory=?, no_tower=(no_tower+1), gpm=?, xpm=?, max_gold=?, max_xp=?, lh=?, denies=?, kills=?, assists=?, deaths=?, kda=?, hDMG=?, tDMG=?, hHEAL=?, l25_time=?, fblood_time=?, total_time=? WHERE rec_type = ? AND steamID = ?;',
                (steamID, matchID, team, hero_id, victory, gpm, xpm, max_gold, max_xp, lh, denies, kills, assists, deaths, kda, hDMG, tDMG, hHEAL, l25_time, fblood_time, total_time, rec_type, steamID,))


        elif rec_type == 'no_deaths':
            self.cur.execute('UPDATE records SET steamID=?, matchID=?, team=?, hero_id=?, victory=?, no_tower=?, gpm=?, xpm=?, max_gold=?, max_xp=?, lh=?, denies=?, kills=?, assists=?, deaths=(deaths+1), kda=?, hDMG=?, tDMG=?, hHEAL=?, l25_time=?, fblood_time=?, total_time=? WHERE rec_type = ? AND steamID = ?;',
                (steamID, matchID, team, hero_id, victory, no_tower, gpm, xpm, max_gold, max_xp, lh, denies, kills, assists, kda, hDMG, tDMG, hHEAL, l25_time, fblood_time, total_time, rec_type, steamID,))


    def store_meta(self, steamID, last_checked=None, victory=None, IRCname=None):
        init = None
        while not init:
            self.cur.execute('SELECT * FROM meta WHERE steamID = ?', (steamID, ))
            init = self.cur.fetchone()
            if not init:
                # here should be at least (SteamID, 0, 0, 0, 0)
                self.cur.execute('INSERT INTO meta VALUES (?, 0, 0, 0, 0)', (steamID,))
                logger.info('Generated new META entry for SteamID {0}'.format(steamID))

        if last_checked > init[1]:
            self.cur.execute('UPDATE meta SET last_checked = ? WHERE steamID = ?', (last_checked, steamID, ))
        if victory:
            self.cur.execute('UPDATE meta SET wins = (wins + 1), games = (games + 1) WHERE steamID = ?', (steamID, ))
        if not victory:
            self.cur.execute('UPDATE meta SET games = (games + 1) WHERE steamID = ?', (steamID, ))
        if IRCname:
            self.cur.execute('UPDATE meta SET IRCname = ? WHERE steamID = ?', (IRCname, steamID))
            logger.info('Updated the IRCname for SteamID{0} to {1}.'.format(steamID, IRCname))


    def get_last_checked(self, steamID):
        self.cur.execute('SELECT last_checked FROM meta WHERE steamID = ?', (steamID, ))
        data = self.cur.fetchone()
        if data:
            return data[0]
        else:
            return


    def table_dropper(self):
        #self.cur.execute('DROP TABLE records;')
        logger.info('Dropped table records.')


    def ircname_to_steamid(self, IRCname):
        '''Returns a SteamID to a certain IRCname.'''
        self.cur.execute('SELECT steamID FROM meta WHERE IRCname = ?', (IRCname,))
        data = self.cur.fetchone()
        return data[0]


    def return_record(self, steamID, record):
        '''Returns a dictionary with all data mapped we need.'''
        self.cur.execute('SELECT * FROM records WHERE steamID = ? AND rec_type=?', (steamID, record))
        data = self.cur.fetchone()

        self.cur.execute('SELECT * FROM meta WHERE steamID = ?', (steamID,))
        meta = self.cur.fetchone()

        data_collect = {
            'steamID': data[0], 'matchID': data[2], 'team': data[3], 'hero_id': data[4],
            'victory': data[5], 'no_tower': data[6], 'gpm': data[7],
            'xpm': data[8], 'max_gold': data[9], 'max_xp': data[10], 'lh': data[11], 'denies': data[12],
            'kills': data[13], 'assists': data[14], 'deaths': data[15], 'kda': data[16], 'hDMG': data[17],
            'tDMG': data[18], 'hHEAL': data[19],
            'l25_time': data[20], 'fblood_time': data[21], 'total_time': data[22],
            }
        meta_collect = {
            'steamID': meta[0], 'last_checked': meta[1], 'wins': meta[2],
            'games': meta[3], 'ircname': meta[4]
             }

        dictionary = {'database': data_collect, 'meta': meta_collect}
        
        return dictionary

    def return_records(self, steamID):
        '''Returns all record-entries for steamID. Does not include meta-data.'''
        self.cur.execute('SELECT * FROM records WHERE steamID = ?;', (steamID,))
        records = self.cur.fetchall()

        return records


logger = logging.getLogger('root')


if __name__ == '__main__':
    logger = log.setup_custom_logger('root') # for working on this module as __main__
    logger = logging.getLogger('root') # for operating this module as submodule
    db = database()
    #db.todolist_match(66332433, 809351753)
    #db.write_match(66332433, 809351753)
    #db.database_print()
    #print db.return_todolist(6633233)
    #print db.return_todolist(db.todolist_steamID())
    #db.store_records(66332433, 1,0,1,1,0,1,999,999,1200,1200,0,1500,1500,1,1,2.0,0,0,0,125,125,125,'no_tower')
    
    #thing = db.return_records(66332433)
    #for line in thing:
    #    print line
    #db.sort_todolist()
    #db.table_dropper()
    #db.ircname_to_steamid('DarkMio')

    print db.return_record(db.ircname_to_steamid('DarkMio'), 'no_tower')
