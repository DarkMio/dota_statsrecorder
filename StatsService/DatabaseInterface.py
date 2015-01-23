from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Boolean


Base = declarative_base()


class Matches(Base):
    __tablename__ = 'matches'

    match_id = Column(Integer, primary_key=True)
    player_id = Column(Integer, primary_key=True)
    # Game Meta:
    win = Column(Boolean)
    duration = Column(Integer)
    tower_status_radiant = Column(Integer)
    tower_status_dire = Column(Integer)
    barracks_status_radiant = Column(Integer)
    barracks_status_dire = Column(Integer)
    cluster = Column(Integer)
    first_blood_time = Column(Integer)
    game_mode = Column(Integer)

    def __repr__(self):
        return "<matches(match_id='%s', player_id='%s', win='%s', duration='%s', tower_status_radiant='%s'," \
               "tower_status_dire='%s', barracks_status_radiant='%s', " \
               "barracks_status_dire='%s', cluster='%s', first_blood_time='%s', game_mode='%s')>" % (
                   self.match_id, self.player_id, self.win, self.duration,
                   self.tower_status_radiant, self.tower_status_dire, self.barracks_status_radiant,
                   self.barracks_status_dire, self.cluster,
                   self.first_blood_time, self.game_mode)


class Player(Base):
    __tablename__ = 'player'
    match_id = Column(Integer, primary_key=True)
    player_id = Column(Integer, primary_key=True)
    hero_id = Column(Integer)
    item_0 = Column(Integer)
    item_1 = Column(Integer)
    item_2 = Column(Integer)
    item_3 = Column(Integer)
    item_4 = Column(Integer)
    item_5 = Column(Integer)
    kills = Column(Integer)
    deaths = Column(Integer)
    assists = Column(Integer)
    leaver_status = Column(Integer)
    gold = Column(Integer)
    last_hits = Column(Integer)
    denies = Column(Integer)
    gold_per_min = Column(Integer)
    xp_per_min = Column(Integer)
    gold_spent = Column(Integer)
    hero_damage = Column(Integer)
    tower_damage = Column(Integer)
    hero_healing = Column(Integer)
    level = Column(Integer)

    def __repr__(self):
        return "<matches(match_id='%s', player_id='%s', hero_id='%s', item_0='%s', item_1='%s', item_2='%s'," \
               "item_3='%s', item_4='%s', item_5='%s', kills='%s', deaths='%s', assists='%s', leaver_status='%s'," \
               "gold='%s', last_hits='%s', denies='%s', gold_per_min='%s', xp_per_min='%s', " \
               "gold_spent='%s', hero_damage='%s', tower_damage='%s', hero_healing='%s', level='%s')>" % (
                   self.match_id, self.player_id, self.hero_id, self.item_0, self.item_1, self.item_2, self.item_3,
                   self.item_4, self.item_5, self.kills, self.deaths, self.assits, self.leaver_status, self.gold,
                   self.last_hits, self.denies, self.gold_per_min, self.xp_per_min, self.gold_spent,
                   self.hero_damage, self.tower_damage, self.hero_healing, self.level)


class AbilityUpgrades(Base):
    __tablename__ = "ability_upgrades"
    match_id = Column(Integer, primary_key=True)
    player_id = Column(Integer, primary_key=True)
    ability = Column(Integer)
    time = Column(Integer)
    level = Column(Integer)

    def __repr__(self):
        return "<ability_upgrades(match_id='%s', player_id='%s', ability=='%s', time='%s', level='%s')>" % (
            self.match_id, self.player_id, self.ability, self.time, self.level)


engine = create_engine('sqlite:///match.db', echo=True)
engine.connect()
Base.metadata.create_all(engine)

void_guy_ability = AbilityUpgrades(match_id=1181212180, player_id=66332433, ability=5184, time=266, level=2)

void_guy = Matches(match_id=1181212180, player_id=66332433, win=True, duration=2927, tower_status_radiant=1926,
                   tower_status_dire=0, barracks_status_radiant=59, barracks_status_dire=0,
                   cluster=133, first_blood_time=133, game_mode=1)

void_guy_hero = Player(match_id=1181212180, player_id=66332433, hero_id=41, item_0=172, item_1=139, item_2=139,
                       item_3=135, item_4=48, item_5=141, kills=23, deaths=6,
                       assists=5, leaver_status=0, gold=5226, last_hits=292, denies=12, gold_per_min=768,
                       xp_per_min=666,
                       gold_spent=34119, hero_damage=25004, tower_damage=7967,
                       hero_healing=0, level=25)

Session = sessionmaker(bind=engine)
session = Session()

# session.add(void_guy)
# session.add(void_guy_hero)
session.add(void_guy_ability)
session.commit()

print void_guy.match_id
print Matches.__table__