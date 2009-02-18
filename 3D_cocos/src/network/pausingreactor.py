# Copyright David Keeney
# Python Software Foundation Licence


import sys
from twisted.python import log, failure, util
from twisted.internet.selectreactor import SelectReactor

class PausingReactor(SelectReactor):
    """Implement selectreactor that can be exited and resumed. """
     
    def __init__(self, *args):
        SelectReactor.__init__(self, *args)
        self._releaseRequested = False
        self._mainLoopGen = None
    
    def _mainLoopGenerater(self):
        """Generater that acts as mainLoop, but yields when
        requested.
        """
        while self.running:
            try:
                while self.running:
                    # Advance simulation time in delayed event
                    # processors.
                    self.runUntilCurrent()
                    t2 = self.timeout()
                    t = self.running and t2
                    self.doIteration(t)

                    if self._releaseRequested:
                        self._releaseRequested = False
                        yield None
            except:
                log.msg("Unexpected error in main loop.")
                log.deferr()
            else:
                log.msg('Main loop terminated.')
 
    def mainLoop(self):
        """Setup mainLoop generater, and initiate looping. """
        self._mainLoopGen = self._mainLoopGenerater()
        self.resume()
    
    def resume(self):
        """Resume mainLoop looping after interruption. """
        try:
            self._mainLoopGen.next()
        except StopIteration:
            pass
        
    def release(self):
        """Request main loop pause and reacter yield to caller. """
        self._releaseRequested = True

    def isRunning(self):
        """Is reactor running? """
        return self.running
        

def install():
    """Configure the twisted mainloop to be run using the pausing reactor.
    """
    reactor = PausingReactor()
    from twisted.internet.main import installReactor
    installReactor(reactor)

    def release():
        reactor.callLater(0, release)
        reactor.release()

    reactor.callLater(0, release)
    #log.startLogging(sys.stdout)
    reactor.run()

__all__ = ['install']
