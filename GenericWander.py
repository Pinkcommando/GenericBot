import asyncio
import traceback
from time import time
from GenericFunctions import *
from GenericBot import GenericBot

class Wander(GenericBot):
	async def onStart(self):
		self.name = "Wander"
		self.startingZone = None
		self.startingPosition = None
		self.operations = self.operation()
		await super().onStart()
		await mark(self)
	
	def operation(self):
		while True:
			yield (healIfNeeded, None, defaultTimeout)
			yield (walkToNearestMob, None, defaultTimeout) 
			yield (battle, None, defaultTimeout) 
			yield (unghost, None, defaultTimeout) 
			yield (eatWisps, None, defaultTimeout)
			
			self.data["count"] += 1
			self.consoleOut()
			
			#if self.data["count"] % 10 == 0: 
			#	yield (quickSellAllPrint, None, defaultTimeout) 
		
	def consoleOut(self):
		os.system('cls' if os.name in ('nt', 'dos') else 'clear')
		
		print(" -- Total Data --- ")
		print(*[f"{a.capitalize()}: {round(self.data[a], 2)}" for a in self.data], sep = "\n")
		
		if not self.running: print("\nBot stopping after current cycle")
		if self.paused: print("\nBot pausing or paused")
		
		print("\n -- Commands --- ")
		print(*[f"{str(self.commands[a][0].__name__).capitalize()}: {a}" for a in self.commands], sep = "\n")
		print()

if __name__ == "__main__":
	async def run():
		wander = Wander()
		try:
			await wander.run()
		except:
			traceback.print_exc()
		await wander.close()
	asyncio.run(run())
