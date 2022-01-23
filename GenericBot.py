import pickle
#import os
import asyncio
from threading import Thread
from time import time
from collections import deque

from wizwalker.extensions.wizsprinter import WizSprinter
from GenericFunctions import checkStartingZone, teleportStart
		
class GenericBot(WizSprinter):
	def __init__(self):
		super().__init__()
		self.combat_handlers = []
		self.running, self.paused = True, False
		self.defaultData = {"count" : 0, "time" : time()}
		self.debug = False
		
		def quit(self):
			self.running = False
		
		self.commands = {"q" : (quit, (self,), {})}
		self.input = UserInput(self)
		self.input.start()

	async def run(self):
		await self.onStart()
		while self.running:
			while self.paused:
				await self.onPause()
			op, t, timeoutFunction = next(self.operations) 
			if self.debug: print(f"running {op.__name__}")
			if t:
				try:
					await asyncio.wait_for(op(self), timeout=t)
				except asyncio.TimeoutError:
					print(op.__name__, "timed out")
					await timeoutFunction(self)
			else:
				await op(self)
			self.saveData()
		self.input.join()
	
	async def onStart(self):
		self.get_new_clients()
		self.clients = self.get_ordered_clients()
		self.loadData()
		for client in self.clients: 
			await client.activate_hooks()
			await client.mouse_handler.activate_mouseless()
		
		for i, p in enumerate(self.clients, 1):
			p.title = self.name + str(i)
		
		await checkStartingZone(self)
		if self.startingPosition != None:
			await teleportStart(self)
		
	# Overwritten by child (usage next(operation) -> (function, timeout seconds, timeout function)
	async def operation(self):
		pass
		
	# Overwritten by child
	async def onPause(self):
		pass
		
	def loadData(self):
		try:
			self.data = pickle.load(open(f"data/{self.name}.p", "rb"))
		except (OSError, IOError) as e:
			self.data = self.defaultData
			pickle.dump(self.data, open(f"data/{self.name}.p", "wb"))
	
	def saveData(self):
		pickle.dump(self.data, open(f"data/{self.name}.p", "wb"))
		
		
	def addCommand(self, command, func, *args, **kwargs):
		self.commands[command] = (func, args, kwargs)
		
	def addData(self, name, defaultValue=0):
		self.data[name] = defaultValue
	

class UserInput(Thread):
	def __init__(self, bot : GenericBot):
		Thread.__init__(self)
		self.bot = bot
		
	def run(self):
		while self.bot.running:
			inp = input()
			if inp in self.bot.commands:
				func, args, kwargs = self.bot.commands[inp]
				func(*args, **kwargs)
		self.bot.running = False # in the event of a keyboard interupt
