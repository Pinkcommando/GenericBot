import asyncio
import os
from time import time
from typing import *
from functools import partial

from wizwalker.constants import Keycode
from wizwalker.extensions.wizsprinter import SprintyCombat, CombatConfigProvider, WizSprinter
from wizwalker.client import Client
from wizwalker.memory import DynamicClientObject
from wizwalker import utils
from wizwalker.errors import MemoryReadError
from wizwalker.extensions.wizsprinter import (CombatConfigProvider, SprintyCombat, WizSprinter)
from wizwalker.utils import XYZ, wait_for_non_error

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

async def eatHealth(self, only_safe: bool = False, excluded_ids: Set[int] = None) -> bool:
	return await go_to_closest_of(self,await self.get_health_wisps(excluded_ids), False)

async def eatMana(self, only_safe: bool = False, excluded_ids: Set[int] = None) -> bool:
	return await go_to_closest_of(self,await self.get_mana_wisps(excluded_ids), False)
	
async def quickSellAllPrint(self, crownItems = False):
	preGold = await asyncio.gather(*[p.stats.current_gold() for p in self.clients])
	await quickSellAll(self, crownItems)
	postGold = await asyncio.gather(*[p.stats.current_gold() for p in self.clients])
	print(*[f"gold: +{post - pre}" for post, pre in zip(postGold, preGold)])

# when crownItems is set to true: all items including crown items will be sold
async def quickSellAll(self, crownItems = False):
	# need to be on first sell page (all items) to function correctly
	await asyncio.gather(*[p.send_key(Keycode.B, .3) for p in self.clients])
	await asyncio.sleep(0.1)
	await click_window_named(self, "QuickSell_Item")
	await asyncio.sleep(0.1)
	await click_window_named(self, "AllAction")
	await asyncio.sleep(0.1)
	# need crown item in inventory to reach this prompt (remove line below if no crown items in inventory)
	await click_window_named(self, "rightButton" if not crownItems else "centerButton")
	await asyncio.sleep(0.1)
	await click_window_named(self, "sellAction")
	await asyncio.sleep(0.1)
	await click_window_named(self, "SellButton")
	await asyncio.sleep(0.1)
	await asyncio.gather(*[p.send_key(Keycode.B, .3) for p in self.clients])
	await asyncio.sleep(0.5)


async def decide_heal(client):
    if await client.needs_potion(health_percent=65, mana_percent=5) and not await client.has_potion():
        print(f'[{client.title}] Needs potion, checking gold count')
        if await client.stats.current_gold() >= 25000: 
            print(f"[{client.title}] Enough gold, buying potions")
            await auto_buy_potions(client)
        else:
            print(f"[{client.title}] Low gold, collecting wisps")
            await collect_wisps(client)
	
async def eatWisps(self):
	for client in self.clients:
			health = await client.stats.max_hitpoints()
			if await client.stats.current_hitpoints() < 0.3 * health:
					await eatHealth(client)
	
	for client in self.clients:
			mana = await client.stats.max_mana()
			if await client.stats.current_mana() < 0.3 * mana:
					await eatMana(client)
			
	await asyncio.sleep(0.1)

async def unghost(self, repeat=7):
	await asyncio.sleep(0.4)
	for _ in range(repeat):
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

def checkDistance(a, b, minDistance):
		dx, dy = abs(a.x - b.x), abs(a.y - b.y)
		return dx < minDistance and dy < minDistance

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
	await asyncio.gather(*[client.teleport(XYZ(x, y, z), False) for client in self.clients])
	
async def teleportStart(self):
	await teleport(self, *self.startingPosition)
	
async def checkStartingZone(self):
	if self.startingZone:
		for client in self.clients:
			zone = await client.zone_name()
			assert zone == self.startingZone
	
async def mark(self):
	await asyncio.gather(*[client.send_key(Keycode.A, 0.1) for client in self.clients])
	await asyncio.sleep(0.01)
	await asyncio.sleep(0.8)
	await asyncio.gather(*[client.send_key(Keycode.PAGE_DOWN, 0.1) for client in self.clients])
	await asyncio.sleep(0.1)
	
async def unmark(self):
	await asyncio.gather(*[client.send_key(Keycode.PAGE_UP, 0.1) for client in self.clients])
	await waitForZoneChange(self)

async def teamup(self):
	await click_window_named(self, "TeamUpButton")
	await asyncio.sleep(0.7)
	await click_window_named(self, "TeamSize4CheckBox")
	await asyncio.sleep(0.1)
	await click_window_named(self, "TeamTypeFarmingCheckBox")
	await asyncio.sleep(0.1)
	await click_window_from_path(self, ["WorldView", "TeamUpConfirmationWindow", "TeamUpConfirmationBackground", "TeamUpButton"])
	
async def waitForZoneChange(self):
	await asyncio.gather(*[client.wait_for_zone_change() for client in self.clients])
	await asyncio.sleep(0.1)

async def battle(self):
	combat_handlers = []
	for client in self.clients: 
		combat_handlers.append(CombatWrapper(client, CombatConfigProvider(f'configs/{client.title}spellconfig.txt', cast_time=0.4))) 
	try:
		await asyncio.gather(*[h.wait_for_combat() for h in combat_handlers]) 
	except: 
		await battle(self)
	await asyncio.sleep(0.1)

async def reset(self):
	await asyncio.gather(*[client.teleport(XYZ(12.702668190002441,1612.439208984375, 0), False) for client in self.clients])
	await asyncio.sleep(0.1)
	await asyncio.gather(*[client.send_key(Keycode.A, 0.1) for client in self.clients])
	await asyncio.sleep(0.1)
	await asyncio.gather(*[client.wait_for_zone_change() for client in self.clients])
	await asyncio.sleep(0.1)
	await asyncio.gather(*[client.goto(-3136.481689453125, 464.997802734375) for client in self.clients])
	await asyncio.sleep(0.7)


async def healIfNeeded(self):
	await asyncio.gather(*[client.use_potion_if_needed(health_percent=65, mana_percent=5) for client in self.clients])
	for client in self.clients:
		if await client.needs_potion(health_percent=65, mana_percent=5) and not await client.has_potion():
			if await client.stats.current_gold() >= 25000: 
				await mark(self)
				await buyPotions(self)
				await unmark(self)
				await mark(self)

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
	
	if not self.running:
		print("Bot stopping after current cycle")
	if self.paused:
		print("Bot pausing or paused")
	
	print("\n --- Commands ---\n\tq: exit\n\tp: pause\n\ts: start")
	
async def goHome(self, cd = 27):
	if hasattr(self, 'teleportCooldown') and time() - self.teleportCooldown < cd:
		await asyncio.sleep(cd - time() + self.teleportCooldown)
	await asyncio.gather(*[client.send_key(Keycode.HOME, 0.1) for client in self.clients])
	await asyncio.gather(*[client.wait_for_zone_change() for client in self.clients])
	self.teleportCooldown = time()
	
async def openWorldGate(self):
	await goHome(self)
	for client in self.clients:
		while not await client.is_in_npc_range():
			await client.send_key(Keycode.S, 0.1)
		await client.send_key(Keycode.X, 0.1)
	await asyncio.sleep(.2)
	
async def goToWizardCity(self):
	await openWorldGate(self)
	for _ in range(5):
		await asyncio.gather(*[client.mouse_handler.click_window_with_name('leftButton') for client in self.clients])
	await asyncio.gather(*[client.mouse_handler.click_window_with_name('wbtnWizardCity') for client in self.clients])
	await asyncio.sleep(0.1)
	await asyncio.gather(*[client.mouse_handler.click_window_with_name('teleportButton') for client in self.clients])
	await asyncio.sleep(0.1)
	await asyncio.gather(*[client.wait_for_zone_change() for client in self.clients])
	
async def spiralTreeToCommons(self):
	await asyncio.gather(*[client.teleport(XYZ(-7.503681, -3141.505859, 244.030518), False) for client in self.clients])
	await asyncio.gather(*[client.send_key(Keycode.A, 0.1) for client in self.clients])
	await asyncio.sleep(0.1)
	await asyncio.gather(*[client.wait_for_zone_change() for client in self.clients])
	await asyncio.gather(*[client.teleport(XYZ(-1.195801, -2155.578125, -153.288666), False) for client in self.clients])
	await asyncio.gather(*[client.send_key(Keycode.A, 0.1) for client in self.clients])
	await asyncio.sleep(0.1)
	await asyncio.gather(*[client.wait_for_zone_change() for client in self.clients])
	
async def teamupTimeout(self):
	await teleportStart(self)
	await asyncio.sleep(0.3)
	try:
		await asyncio.wait_for(teamup(self), timeout=30)
	except asyncio.TimeoutError:
		print("teamup failed again, trying again")
		await teamupTimeout(self)
	
async def buyPotions(self):
	await goToWizardCity(self)
	await spiralTreeToCommons(self)
	# TP to potion vendor
	await teleport(self, -4352.091797, 1111.261230, 229.000793)
	await asyncio.gather(*[client.send_key(Keycode.A, 0.1) for client in self.clients])
	await asyncio.sleep(0.5)
	
	for client in self.clients:
		while not await client.is_in_npc_range():
			await teleport(self, -4352.091797, 1111.261230, 229.000793)
			await asyncio.gather(*[client.send_key(Keycode.A, 0.1) for client in self.clients])
			await asyncio.sleep(.5)
		await client.send_key(Keycode.X, 0.1)
	
	await asyncio.gather(*[client.send_key(Keycode.X, 0.1) for client in self.clients])
	await asyncio.sleep(1) 
	
	windows = [
		"fillallpotions",
		"buyAction",
		"btnShopPotions",
		"centerButton",
		"fillonepotion",
		"buyAction",
		"exit"
	]
	
	# Buy potions
	for window in windows:
		await asyncio.gather(*[client.mouse_handler.click_window_with_name(window) for client in self.clients])
		await asyncio.sleep(1)
		
async def needs_mana(self, mana_percent: int = 10) -> bool:
	return await self.calc_mana_ratio() * 100 <= mana_percent

async def needs_health(self, health_percent: int = 20) -> bool:
	return await self.calc_health_ratio() * 100 <= health_percent

async def calc_health_ratio(self) -> float:
	return await self.stats.current_hitpoints() / await self.stats.max_hitpoints()

@staticmethod
async def calc_mana_ratio(self) -> float:
	return await self.stats.current_mana() / await self.stats.max_mana()

class CombatWrapper(SprintyCombat):
	async def get_client_member(self):
		return await utils.wait_for_non_error(super().get_client_member)
		
async def defaultTimeout(*args, **kwargs):
	return