"""
pysat._queue - provides thread safe operations
=========================================

This module enables pysat to run sequential operations in a separate 
thread. This is useful for IO operations which may need to be run
sequentially.

This module implements a @queued decorator, which can be attached
to any function that should be added to the pysat_queue. The
pysat_queue is processed by a separate task_runner Thread,
which spends most of its time waiting for new tasks.

The task_runner thread will start when this
module or one of its members is imported. 
"""

from decorator import decorator, decorate
from threading import Thread
from queue import Queue


# class PropagatingThread(Thread):
#     def run(self):
#         self.exc = None
#         try:
#             if hasattr(self, '_Thread__target'):
#                 # Thread uses name mangling prior to Python 3.
#                 self.ret = self._Thread__target(*self._Thread__args, **self._Thread__kwargs)
#             else:
#                 self.ret = self._target(*self._args, **self._kwargs)
#         except BaseException as e:
#             self.exc = e

#     def join(self):
#         super(PropagatingThread, self).join()
#         if self.exc:
#             raise self.exc
#         return self.ret


pysat_queue = Queue()

def task_master(q):
    """Runs the tasks in the queue on a separate thread
    
    Results are returned in the function's return_queue attribute
    """
    while True:
        f, args, kwargs = q.get()
        try:
            result = f(*args, **kwargs)
            f.return_queue.put(result)
        except Exception as exception:
            f.return_queue.put(exception)
        q.task_done()
        
task_runner = Thread(
    target = task_master, 
    name = 'pysat_task_runner',
    args = (pysat_queue,))

task_runner.setDaemon(True)
task_runner.start()

def decorator_wrapper(f, *args, **kwargs):
    """Wrapper needed by decorator.decorate to pass through args, kwargs"""
    pysat_queue.put((f, args, kwargs))
    return f.return_queue.get()


def queued(_func = None, return_queue = None):
    """Registers function in pysat queue and optionally returns results to passed in queue
    """
    def decorator_queued(f):
        # decorate preserves the function signature
        if return_queue is not None:
            f.return_queue = return_queue
        elif hasattr(f, 'return_queue'):
            pass
        else:
            f.return_queue = Queue()
        return decorate(f, decorator_wrapper) 

    if _func is None:
        return decorator_queued
    else:
        return decorator_queued(_func)