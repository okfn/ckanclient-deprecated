from threading import Thread
from datetime import datetime
from string import ascii_letters, digits
from random import choice
from pprint import pprint
import logging
import sys

from ckanclient import CkanClient

class Hammer(Thread):
    stats = {}
    def __init__(self, *av, **kw):
        super(Hammer, self).__init__(target=self.doit, args=av, kwargs=kw)

    def rndname(self):
        return "".join(map(lambda x: choice(ascii_letters + digits), range(16))) 

    def elapsed(self, interval):
        seconds = float(interval.seconds)
        useconds = float(interval.microseconds)/1000000
        return seconds + useconds

    def doit(self, count):
        log = logging.getLogger("hammer/%s" % self.getName())
        log.info("starting")

        collector = self.stats.setdefault(self.getName(), {})
        collector["count"] = count

        ckan = CkanClient(
                base_location="http://test.ckan.net/api",
                api_key="e5b7ae68-a279-42fc-82ec-212fa32a68fc"
        )

        tags = [self.rndname() for x in range(16)]

        packages = []
        start = datetime.now()
        for i in range(count):
            name = self.rndname()
            data = {
                    "name": name,
                    "title": "Test %s" % name,
                    "extras": {"hammer": "yes"}
            }
            ckan.package_register_post(data)
            packages.append(data)
        end = datetime.now()
        interval = end-start
        elapsed = self.elapsed(interval)
        collector["post"] = elapsed
        log.info("registered %d packages in %s: %s pkg/sec" %
                (count, interval, float(count)/elapsed))

        start = datetime.now()            
        for data in packages:
            data["tags"] = list(set([choice(tags) for x in range(4)]))
            ckan.package_entity_put(data)
        end = datetime.now()
        interval = end-start
        elapsed = self.elapsed(interval)
        collector["put"] = elapsed
        log.info("tagged %d packages in %s: %s pkg/sec" %
                (count, interval, float(count)/elapsed))

        start = datetime.now()            
        for data in packages:
            ckan.package_entity_get(data["name"])
        end = datetime.now()
        interval = end-start
        elapsed = self.elapsed(interval)
        collector["get"] = elapsed
        log.info("retrieved %d packages in %s: %s pkg/sec" %
                (count, interval, float(count)/elapsed))

        start = datetime.now()
        for data in packages:
           ckan.package_entity_delete(data["name"])
        end = datetime.now()
        interval = end-start
        elapsed = self.elapsed(interval)
        collector["delete"] = elapsed
        log.info("deleted %d packages in %s: %s pkg/sec" %
                (count, interval, float(count)/elapsed))

        log.info("done")

    @classmethod
    def report(self):
        log = logging.getLogger("hammer")
        nthreads = len(self.stats.keys())
        count = float(sum([self.stats[k]["count"] for k in self.stats]))
        for stat in ("get", "put", "post", "delete"):
            total = sum([self.stats[k][stat] for k in self.stats])
            log.info("average %s: %s pkg/sec" % (stat, count/total))

if __name__ == '__main__':
    """
    Usage: %prog nthreads count

    Benchmark test.ckan.net with nthreads concurrency performing
    get/put/post/delete operations count times
    """
    logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s"
    )

    try:
        nthreads = int(sys.argv[1])
    except IndexError:
        nthreads = 1

    try:
        count = int(sys.argv[2])
    except IndexError:
        count = 1

    threads = [Hammer(count) for x in range(nthreads)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    Hammer.report()
