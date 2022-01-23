import asyncio
import traceback
from time import time
from GenericFunctions import *
from GenericBot import GenericBot
from wizwalker import ClientHandler, Keycode

class TestBot(GenericBot):
	async def onStart(self):
		self.name = "TestBot"
		await super().onStart()
		#await goHome(self)
		#await goToWizardCity(self)
		#await buyPotions(self)
		#await checkHealthMana(self)
		#await self.clients[0].root_window.debug_print_ui_tree()
		#await TestBot.read(self.clients[0])
	
	async def read(client):

		# to find this window you can use await client.root_window.debug_print_ui_tree()
		# window that contains the fish current space used and max space
		possiple_windows = await client.root_window.get_windows_with_name("pat1")

		if not possiple_windows:
			print("Couldn't find the space used!")
		else:
			#print(dir(possiple_windows[0]))
			for window in possiple_windows:
				print(await window.maybe_text())

	async def onLoop(self):
		pass
	
if __name__ == "__main__":
	async def run():
		testbot = TestBot()
		try:
			await testbot.run()
		except:
			traceback.print_exc()
		await testbot.close()
	asyncio.run(run())
