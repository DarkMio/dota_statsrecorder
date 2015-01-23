import sqlite3
import threading
import logging
import argparse

from time import time, sleep

# a

class Multithread(object):
    def __init__(self):
        self.running = True
        self.threads = []

    def go(self):
        t1 = threading.Thread(target=None)
        t2 = threading.Thread(target=None)
        t3 = threading.Thread(target=None)
        # Make threads daemonic, i.e. terminate them when main thread
        # terminates. From: http://stackoverflow.com/a/3788243/145400
        t1.daemon = True
        t2.daemon = True
        t3.daemon = True
        t1.start()
        t2.start()
        t3.start()
        self.threads.append(t1)
        self.threads.append(t2)
        self.threads.append(t3)


class NoParsingFilter(logging.Filter):
    def filter(self, record):
        return not record.getMessage().startswith('Resetting')


def join_threads(threads):
    """
    Join threads in interruptable fashion.
    From http://stackoverflow.com/a/9790882/145400
    """
    for t in threads:
        while t.isAlive():
            t.join(5)


def check(ID):
    check = cur.execute('SELECT id FROM reddit WHERE id = "%s" LIMIT 1' % ID)
    for line in check:
        sleep(10)
        if line:
            return True


def add(ID):
    cur.execute('INSERT INTO reddit (time, id) VALUES ("%s", "%s")' % (int(time()), ID))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='MassdropBot parses Links which are more comfy to click in the comment-section.')
    parser.add_argument('--verbose', action='store_true', help='Print mainly tracebacks.')
    args = parser.parse_args()

    # SET UP LOGGER
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', datefmt='%X',
                        level=logging.DEBUG if args.verbose else logging.INFO)
    log = logging.getLogger(__name__)
    log.addFilter(NoParsingFilter())

    # SET UP DATABASE
    db = sqlite3.connect('massdrop.db', check_same_thread=False, isolation_level=None)
    cur = db.cursor()

    t = Multithread()

    t.go()

    try:
        join_threads(t.threads)
    except KeyboardInterrupt:
        log.info("Stopping process entirely.")
        db.close()  # you can't close it enough, seriously.
        log.info("Established connection to database was closed.")