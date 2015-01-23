import Queue


class DatabaseQueue(object):
    q = None    # Will hold the Queue Object.

    def __init__(self):
        self.q = Queue.Queue()

    def append(self, item):
        self.q.put(item)

    def get(self):
        if not self.empty():
            return self.q.get()
        else:
            raise Exception("Exception Underflow: Queue is empty, therefore there is nothing to get.")

    def empty(self):
        return self.q.empty()

if __name__ == "__main__":
    q = DatabaseQueue()
    q.append("Text.")
    print "Empty equals", q.empty()
    var = q.get()
    print var
    try:
        print "Empty equals", q.empty()
        q.get()
    except Exception as e:
        print e
