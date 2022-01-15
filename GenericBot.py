import pickle
import os
from threading import Thread
from time import time

from wizwalker.extensions.wizsprinter import WizSprinter
		
class GenericBot(WizSprinter):
	def __init__(self):
		super().__init__()
		self.combat_handlers = []
		self.start, self.count, self.total = 0, 0, time()
		self.running, self.paused = True, False
		
		def quit(self):
			self.running = False
		
		self.commands = {"q" : (quit, self)}
		self.input = UserInput(self)
		self.input.start()
		
		try:
			self.data = pickle.load(open( "save.p", "rb"))
		except (OSError, IOError) as e:
			self.data = {"count" : 0, "time" : 0}
			pickle.dump(self.data, open( "save.p", "wb"))

	async def run(self):
		await self.onStart()
		while self.running:
			while self.paused:
				await self.onPause()
			prev = time()
			await self.onLoop()
			self.count += 1
			await self.consoleOut(prev, self.saveData())
		self.input.join()
	
	async def onStart(self):
		self.get_new_clients()
		self.clients = self.get_ordered_clients()
		for client in self.clients: 
			await client.activate_hooks()
			await client.mouse_handler.activate_mouseless()
		
		for i, p in enumerate(self.clients, 1):
			p.title = self.name + str(i)
	
	# Overwritten by child
	async def onLoop(self):
		pass
		
	# Overwritten by child
	async def onPause(self):
		pass
		
	def saveData(self):
		cur = round((time() - self.start) / 60, 2)
		self.data["count"] += 1
		self.data["time"] += cur
		pickle.dump(self.data, open( "save.p", "wb"))
		return cur
		
		
	async def consoleOut(self, prev, cur):
		os.system('cls' if os.name in ('nt', 'dos') else 'clear')
		
		if self.count:
			print(" --- Session Data --- ")
			print("Count:", self.count)
			print("Time:", round((prev - self.total) / 60, 2), "minutes")
			print()
		'''
			print(" -- Total Data --- ")
			print(*[f"{a.capitalize()}: {round(self.data[a], 2)}" for a in self.data], sep = "\n")
			print("Average:", round(self.data["time"] / self.data["count"], 2), "minutes")
			print()
		'''
		if not self.running:
			print("Bot stopping after current cycle")
		if self.paused:
			print("Bot pausing or paused")
		
		print(" -- Commands --- ")
		print(*[f"{str(self.commands[a][0].__name__).capitalize()}: {a}" for a in self.commands], sep = "\n")
	

class UserInput(Thread):
	def __init__(self, bot : GenericBot):
		Thread.__init__(self)
		self.bot = bot
		
	def run(self):
		while self.bot.running:
			inp = input()
			if inp in self.bot.commands:
				self.bot.commands[inp][0](self.bot.commands[inp][1])
		self.bot.running = False # in the event of a keyboard interupt
