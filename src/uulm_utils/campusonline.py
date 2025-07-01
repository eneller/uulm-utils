import questionary
from playwright.async_api import Locator, Browser, BrowserContext
import asyncclick as click
import questionary

import asyncio
from enum import Enum
import csv

from uulm_utils.common import cli, browser_options, run_playwright
Selection = Enum('Selection', ['TREE_WALK', 'TREE_LEAF', 'ITEM_SELECTED'])
CAMPUSONLINE_LOC = 'li.treelist > a'

async def selection_or_walk(locators: list[Locator]):
    option_walk = questionary.Choice(title= 'Walk the Tree from here', value=Selection.TREE_WALK, checked=True)
    options = [option_walk] + [questionary.Choice(title=await loc.inner_text(), value=loc) for loc in locators]
    selection = await questionary.select(choices=options, message='Select one of the following options').ask_async()
    if selection == Selection.TREE_WALK:
        return selection, None
    else: return Selection.ITEM_SELECTED, selection
    
async def walk_tree(loc: Locator, browser: Browser, context: BrowserContext, path: list[str]=[]):
    page = await browser.new_page()
    locators = await loc.locator(CAMPUSONLINE_LOC).all()
    if len(locators) == 0:
    # at single course level
        await loc.locator('a:nth-child(9)').click()
        await asyncio.sleep(20)
        return [dict()]
    return [item for l in locators for item in (await walk_tree(l, browser, context))]
    

@cli.command()
@click.argument('filename', type=click.Path())
@browser_options
async def campusonline(filename, username, password, headless):
    '''
    Export modules from Campusonline as CSV.
    '''
    path: list[str] = []
    async for browser, context in run_playwright(headless):
        page = await context.new_page()
        # login
        await page.goto("https://campusonline.uni-ulm.de")
        await page.get_by_role("textbox", name="Benutzerkennung").click()
        await page.get_by_role("textbox", name="Benutzerkennung").fill(username)
        await page.get_by_role("textbox", name="Passwort").fill(password)
        await page.get_by_role("button", name="Anmelden").click()
        await page.get_by_role("link", name="Studium").click()
        await page.get_by_role("link", name="Modulbeschreibungen ansehen").click()
        sel = 0
        # first select your study path
        while True:
            options = await page.locator(CAMPUSONLINE_LOC).all()
            sel, loc= await selection_or_walk(options)
            if sel == Selection.TREE_WALK:
                break
            loc = cast(Locator, loc)
            path.append(await loc.inner_text())
        # then walk tree
        courses = await walk_tree(loc, browser, context)
        with open(filename, "w", newline="") as f:
            w = csv.DictWriter(f, courses.keys())
            w.writeheader()
            w.writerow(courses)
    return
