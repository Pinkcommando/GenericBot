import asyncio
import traceback
from time import time
from GenericFunctions import *
from GenericBot import GenericBot

'''

	Not very well tested
	
		running test 1: 1/20/2022 12:36 AM [Worked on small test]
		running test 2: 1/20/2022 3:08 AM 
		
		test 3: 1/20/2022 4:20 PM (Team up still can fail, attemting a teleport to sigil)

		
	TODO:
		change functions to check for zone names
		functions should have a return value based on if the were successful
			return value True == successful
			return value False == failure

'''

class Loremaster(GenericBot):
	async def onStart(self):
		self.name = "Loremaster"
		self.startingZone = None #"DragonSpire/DS_A1_Knowledge/Interiors/DS_Library_Interior"
		self.startingPosition = (-3135, 465, 0)		# Starting position TODO: None -> don't teleport 
		self.operations = self.operation()
		await super().onStart()
		await mark(self)
	
	def operation(self):
		while True:
			yield (healIfNeeded, None, defaultTimeout)
			yield (teamup, 10, teamupTimeout)
			yield (waitForZoneChange, None, defaultTimeout)
			yield (walkToNearestMob, None, defaultTimeout)
			yield (battle, None, defaultTimeout)
			yield (reset, None, defaultTimeout)
			
			self.data["count"] += 1
			print(f"Run count: {self.data['count']}")
			if self.data["count"] % 10 == 9:
				yield (quickSellAllPrint, None, defaultTimeout)
	
if __name__ == "__main__":
	async def run():
		loremaster = Loremaster()
		try:
			await loremaster.run()
		except:
			traceback.print_exc()
		await loremaster.close()
	asyncio.run(run())
