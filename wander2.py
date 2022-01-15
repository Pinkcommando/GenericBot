import asyncio
import traceback
from time import time
from wizextra import *
from GenericBot import GenericBot

class Wander(GenericBot):
	async def onStart(self):
		self.name = "Wander"
		await super().onStart()

	async def onLoop(self):
		await unghost(self)
		await walkToNearestMob(self)
		await battle(self)
		await wisp_heal(self)
		if self.count % 20 == 19: 
			await quickSellAll(self)
	
if __name__ == "__main__":
	async def run():
		wander = Wander()
		try:
			await wander.run()
		except:
			traceback.print_exc()
		await wander.close()
	asyncio.run(run())
