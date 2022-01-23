import asyncio
import traceback
from time import time
from GenericFunctions import *
from GenericBot import GenericBot

class BotTemplate(GenericBot):
	async def onStart(self):
		self.name = "BotName" 					# Bot name
		self.startingZone = None  				# Starting zone (ex. "Location/a/b/c")
		self.startingPosition = (0, 0, 0)		# Starting position TODO: None -> don't teleport 
		self.operations = self.operation()
		await super().onStart()
		await mark(self)
	
	def operation(self):
		while True:
			### Add bot functions here
			#yield (function, timeoutTime, timeoutFunction) #(example)
			
			### Keep track of data here
			self.data["count"] += 1
			print(f"Run count: {self.data['count']}")
			
			### Quicksell
			if self.data["count"] % 10 == 0: 
				yield (quickSellAllPrint, None, defaultTimeout) 
	
if __name__ == "__main__":
	async def run():
		bot = BotTemplate()
		try:
			await bot.run()
		except:
			traceback.print_exc()
		await bot.close()
	asyncio.run(run())
