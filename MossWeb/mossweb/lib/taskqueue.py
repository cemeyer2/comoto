import threading
from Queue import Queue

#http://code.activestate.com/recipes/475160/
#modified 6 oct 2010 by charlie meyer to avoid nasty inheritance bug with new versions of python
class TaskQueue(Queue):

    def __init__(self):
        Queue.__init__(self)        
        self.all_tasks_done = threading.Condition(self.mutex)
        self.tq_unfinished_tasks = 0

    def _put(self, item):
        Queue._put(self, item)
        self.tq_unfinished_tasks += 1        

    def task_done(self):
        """Indicate that a formerly enqueued task is complete.

        Used by Queue consumer threads.  For each get() used to fetch a task,
        a subsequent call to task_done() tells the queue that the processing
        on the task is complete.

        If a join() is currently blocking, it will resume when all items
        have been processed (meaning that a task_done() call was received
        for every item that had been put() into the queue).

        Raises a ValueError if called more times than there were items
        placed in the queue.
        """
        self.all_tasks_done.acquire()
        try:
            unfinished = self.tq_unfinished_tasks - 1
            if unfinished <= 0:
                if unfinished < 0:
                    raise ValueError('task_done() called too many times')
                self.all_tasks_done.notifyAll()
            self.tq_unfinished_tasks = unfinished
        finally:
            self.all_tasks_done.release()

    def join(self):
        """Blocks until all items in the Queue have been gotten and processed.

        The count of unfinished tasks goes up whenever an item is added to the
        queue. The count goes down whenever a consumer thread calls task_done()
        to indicate the item was retrieved and all work on it is complete.

        When the count of unfinished tasks drops to zero, join() unblocks.
        """
        self.all_tasks_done.acquire()
        try:
            while self.tq_unfinished_tasks:
                self.all_tasks_done.wait()
        finally:
            self.all_tasks_done.release()