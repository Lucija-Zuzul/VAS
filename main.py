import asyncio
from spade import quit_spade
import sys
from aukcioner import Aukioner
from kupac import Kupac

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if __name__ == '__main__':
    aukcioner = Aukioner("aukcioner@localhost", "1234", kupac1="kupac1@localhost", kupac2="kupac2@localhost")
    kupac1 = Kupac("kupac1@localhost", "1234", naziv="KUPAC 1", aukcioner="aukcioner@localhost",
    kupac_protivnik="kupac2@localhost", budzet=1000, limit=500)
    kupac2 = Kupac("kupac2@localhost", "1234", naziv="KUPAC 2", aukcioner="aukcioner@localhost",
    kupac_protivnik="kupac1@localhost", budzet=1000, limit=300)

    kupac1_start = kupac1.start()
    kupac1_start.result()

    kupac2_start = kupac2.start()
    kupac2_start.result()

    aukcioner_start = aukcioner.start()
    aukcioner_start.result()

    input("Press ENTER to exit.\n")
    kupac1.stop()
    kupac2.stop()
    aukcioner.stop()
    quit_spade()