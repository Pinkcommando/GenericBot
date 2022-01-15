import asyncio
import traceback
from time import time
from wizextra import *
from GenericBot import GenericBot

class Loremaster(GenericBot):
	async def onStart(self):
		self.name = "Loremaster"
		await super().onStart()
		await teleport(self, -3136.481689453125, 464.997802734375, 0)
		await mark(self)

	async def onLoop(self):
		await run_manahpcheck(self)
		await run_teamup(self)
		await walkToNearestMob(self)
		await run_battle(self)
		await run_reset(self)
		await run_timer(self)
	
if __name__ == "__main__":
	async def run():
		loremaster = Loremaster()
		try:
			await loremaster.run()
		except:
			traceback.print_exc()
		await loremaster.close()
	asyncio.run(run())
