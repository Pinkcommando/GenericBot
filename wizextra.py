import asyncio
import os
from time import time
from typing import *
from wizwalker.constants import Keycode
from wizwalker.extensions.wizsprinter import SprintyCombat, CombatConfigProvider, WizSprinter
from wizwalker.client import Client
from wizwalker.memory import DynamicClientObject


from functools import partial

from wizwalker import utils
from wizwalker.errors import MemoryReadError
from wizwalker.extensions.wizsprinter import (CombatConfigProvider, SprintyCombat, WizSprinter)
from wizwalker.utils import XYZ, wait_for_non_error

from utils import (auto_buy_potions, collect_wisps, decide_heal,
					 get_window_from_path, safe_tp_to_health, safe_tp_to_mana)

def clearConsole():
	os.system('cls' if os.name in ('nt', 'dos') else 'clear')


async def go_to_closest_mob(self, excluded_ids: Set[int] = None) -> bool:
	return await go_to_closest_of(self, await self.get_mobs(excluded_ids), False)

async def go_to_closest_of(self, entities: List[DynamicClientObject], only_safe: bool = False):
	if e := await self.find_closest_of_entities(entities, only_safe):
		ev = await e.location()
		await self.goto(ev.x, ev.y)
		return True
	return False

async def go_to_closest_health_wisp(self, only_safe: bool = False, excluded_ids: Set[int] = None) -> bool:
	return await go_to_closest_of(self,await self.get_health_wisps(excluded_ids), False)

async def go_to_closest_mana_wisp(self, only_safe: bool = False, excluded_ids: Set[int] = None) -> bool:
	return await go_to_closest_of(self,await self.get_mana_wisps(excluded_ids), False)

async def quickSellAll(self, crownItems = False):
	await asyncio.gather(*[p.send_key(Keycode.B, .3) for p in self.clients])
	await click_window_named(self, "QuickSell_Item")
	await click_window_named(self, "AllAction")
	if not crownItems: await click_window_named(self, "rightButton")
	else: await click_window_named(self, "centerButton")
	await click_window_named(self, "sellAction")
	await click_window_named(self, "SellButton")
	await asyncio.gather(*[p.send_key(Keycode.B, .3) for p in self.clients])
	
	
async def wisp_heal(self):
	for p in self.clients:
			total_health=await p.stats.max_hitpoints()
			if await p.stats.current_hitpoints() < 0.3 * total_health:
					await go_to_closest_health_wisp(p)
	
	for p in self.clients:
			total_mana=await p.stats.max_mana()
			if await p.stats.current_mana() < 0.3 * total_mana:
					await go_to_closest_mana_wisp(p)
			
	await asyncio.sleep(0.1)
	await asyncio.gather(*[p.use_potion_if_needed(health_percent=10, mana_percent=5) for p in self.clients]) 
	await asyncio.gather(*[decide_heal(p) for p in self.clients])
	await asyncio.sleep(5)

async def unghost(self):
	await asyncio.sleep(0.4)
	await asyncio.gather(*[p.send_key(Keycode.S, .3) for p in self.clients])
	await asyncio.gather(*[p.send_key(Keycode.W, .3) for p in self.clients])

async def walkToNearestMob(self):
	await go_to_closest_mob(self.clients[0])
	p1 = await self.clients[0].body.position()
	for p in self.clients[1:]:
		await p.goto(p1.x, p1.y)
		await p.send_key(Keycode.W, 0.1)
		await asyncio.sleep(0.2)

async def battle(self):
	combat_handlers = []
	for p in self.clients: 
		combat_handlers.append(SprintyCombat(p, CombatConfigProvider(f'configs/{p.title}spellconfig.txt', cast_time=2,)))
	await asyncio.gather(*[h.wait_for_combat() for h in combat_handlers])

def check_position_near(xyz_one, xyz_two, nearness):
		x_nearness = abs(xyz_one.x - xyz_two.x)
		y_nearness = abs(xyz_one.y - xyz_two.y)
		
		return x_nearness < nearness and y_nearness < nearness

async def get_window_from_path(root_window, name_path):
	async def _recurse_follow_path(window, path):
		if len(path) == 0:
			return window

		for child in await window.children():
			if await child.name() == path[0]:
				found_window = await _recurse_follow_path(child, path[1:])
				if not found_window is False:
					return found_window

		return False

	return await _recurse_follow_path(root_window, name_path)

async def click_window_from_path(self, path_array):
	for client in self.clients:
		coro = partial(get_window_from_path, client.root_window, path_array)
		window = await utils.wait_for_non_error(coro)
		await client.mouse_handler.click_window(window)

async def click_window_named(self, button_name):
	for client in self.clients:
		coro = partial(client.mouse_handler.click_window_with_name, button_name)
		await utils.wait_for_non_error(coro)
	
async def teleport(self, x=0, y=0, z=0):
	# Go to starting area
	await asyncio.gather(*[client.teleport(XYZ(x, y, z), False) for client in self.clients])
	
async def mark(self):
	await asyncio.gather(*[client.send_key(Keycode.A, 0.1) for client in self.clients])
	await asyncio.sleep(0.01)
	await asyncio.sleep(0.8)
	await asyncio.gather(*[client.send_key(Keycode.PAGE_DOWN, 0.1) for client in self.clients])
	await asyncio.sleep(0.1)

async def run_teamup(self):
	# Click Team Up, Farming, and minimum of 4 buttons
	await click_window_named(self, "TeamUpButton")
	await asyncio.sleep(0.7)
	await click_window_named(self, "TeamSize4CheckBox")
	await asyncio.sleep(0.1)
	await click_window_named(self, "TeamTypeFarmingCheckBox")
	await asyncio.sleep(0.1)
	await click_window_from_path(self, ["WorldView", "TeamUpConfirmationWindow", "TeamUpConfirmationBackground", "TeamUpButton"])
	
	# Wait for zone change
	await asyncio.gather(*[client.wait_for_zone_change() for client in self.clients])
	await asyncio.sleep(0.1)

async def run_lore_battleTP(self):
	await asyncio.gather(*[client.teleport(XYZ(-46.86019515991211, -28.653949737548828, 0), False) for client in self.clients])
	await asyncio.sleep(0.1)
	await asyncio.gather(*[client.send_key(Keycode.A, 0.1) for client in self.clients])
	await asyncio.sleep(0.1)

async def run_battle(self):
	# Battle:
	combat_handlers = []
	for client in self.clients: # Setting up the parsed configs to combat_handlers
		combat_handlers.append(SeanNoLikeMobs(client, CombatConfigProvider(f'configs/{client.title}spellconfig.txt', cast_time=0.4))) 
	try:
		await asyncio.gather(*[h.wait_for_combat() for h in combat_handlers]) # .wait_for_combat() to wait for combat to then go through the battles
	except: #Exception e:
		#print(e)
		await self.run_battle()
	await asyncio.sleep(0.1)

async def run_reset(self):
	await asyncio.gather(*[client.teleport(XYZ(12.702668190002441,1612.439208984375, 0), False) for client in self.clients])
	await asyncio.sleep(0.1)
	await asyncio.gather(*[client.send_key(Keycode.A, 0.1) for client in self.clients])
	await asyncio.sleep(0.1)
	await asyncio.gather(*[client.wait_for_zone_change() for client in self.clients])
	await asyncio.sleep(0.1)
	await asyncio.gather(*[client.goto(-3136.481689453125, 464.997802734375) for client in self.clients])
	await asyncio.sleep(0.7)

async def run_manahpcheck(self):
	# Healing
	await asyncio.gather(*[client.use_potion_if_needed(health_percent=65, mana_percent=5) for client in self.clients])
	await asyncio.gather(*[decide_heal(client) for client in self.clients])
	await asyncio.sleep(1.5)

async def run_timer(self):
	# Time
	self.data["count"] += 1
	pickle.dump(self.data, open( "save.p", "wb"))

def conPrint(self, msg, i=0):
	clearConsole()
	
	if self.cur:
		print(" --- Session Data --- ")
		print("Count:", self.total_count)
		print("Time:", round((self.prev - self.total) / 60, 2), "minutes")
		print("Average:", round(((self.prev - self.total) / 60) / self.total_count, 2), "minutes")
		print("Last run time: ", self.cur, "minutes\n")
	
		print(" -- Total Data --- ")
		print(*[f"{a.capitalize()}: {round(self.data[a], 2)}" for a in self.data], sep = "\n")
		print("Average:", round(self.data["time"] / self.data["count"], 2), "minutes")
		print()
	
	print(f"Progress: [{'x'*i}{' '*(4-i)}] {msg}")
	#for client in self.clients:
	#	zone = client.zone_name()
	#	print(f"Current zone: {zone}")
	if not self.running:
		print("Bot stopping after current cycle")
	if self.paused:
		print("Bot pausing or paused")
	
	print("\n --- Commands ---\n\tq: exit\n\tp: pause\n\ts: start")
	

async def auto_buy_potions_TP(self):
	return
	# Head to home world gate
	await asyncio.sleep(0.1)
	await self.send_key(Keycode.HOME, 0.1)
	await self.wait_for_zone_change()
	while not await self.is_in_npc_range():
		await self.send_key(Keycode.S, 0.1)
	await self.send_key(Keycode.X, 0.1)
	await asyncio.sleep(1.2)
	# Go to Wizard City
	await self.mouse_handler.click_window_with_name('wbtnWizardCity')
	await asyncio.sleep(0.3)
	await self.mouse_handler.click_window_with_name('teleportButton')
	await self.wait_for_zone_change()
	await asyncio.sleep(0.3)
	# TP to potion vendor
	await self.teleport(XYZ(-7.503681, -3141.505859, 244.030518), False)
	await self.send_key(Keycode.A, 0.1)
	await asyncio.sleep(0.1)
	await self.wait_for_zone_change()
	await self.teleport(XYZ(-1.195801, -2155.578125, -153.288666), False)
	await self.send_key(Keycode.A, 0.1)
	await asyncio.sleep(0.1)
	await self.wait_for_zone_change()
	await self.teleport(XYZ(-4352.091797, 1111.261230, 229.000793), False)
	await self.send_key(Keycode.A, 0.1)
	await asyncio.sleep(0.5)
	if not await self.is_in_npc_range():
		await self.teleport(XYZ(-4352.091797, 1111.261230, 229.000793), False)
		await self.send_key(Keycode.A, 0.1)
		await asyncio.sleep(3.5)
	await self.send_key(Keycode.X, 0.1)
	await asyncio.sleep(1) 
	# Buy potions
	for i in self.potion_ui_buy:
		await self.mouse_handler.click_window_with_name(i)
		await asyncio.sleep(1)
	# Return to marker
	await self.send_key(Keycode.PAGE_UP, 0.1)
	await self.wait_for_zone_change()
	await self.send_key(Keycode.PAGE_DOWN, 0.1)
	if await self.needs_mana(mana_percent=5):
		await self.collect_quick_manawisps()

async def needs_mana(self, mana_percent: int = 10) -> bool:
	return await self.calc_mana_ratio() * 100 <= mana_percent

async def needs_health(self, health_percent: int = 20) -> bool:
	return await self.calc_health_ratio() * 100 <= health_percent

async def calc_health_ratio(self) -> float:
	"""Simply returns current health divided by max health"""
	return await self.stats.current_hitpoints() / await self.stats.max_hitpoints()

@staticmethod
async def calc_mana_ratio(self) -> float:
	"""Simply returns current health divided by max health"""
	return await self.stats.current_mana() / await self.stats.max_mana()

# Fix for CombatMember Error -Thanks to Starrfox
class SeanNoLikeMobs(SprintyCombat):
	async def get_client_member(self):
		return await utils.wait_for_non_error(super().get_client_member)