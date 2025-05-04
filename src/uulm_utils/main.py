import csv
from typing import cast
import asyncclick as click
import questionary
from playwright.async_api import Browser, BrowserContext, Locator, Page, async_playwright
import pandas as pd
from dotenv import load_dotenv


from enum import Enum
import asyncio
from time import sleep
import logging
from datetime import datetime, timedelta


load_dotenv()  # take environment variables
logger = logging.getLogger(__name__)

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
    
async def run_playwright(headless: bool):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=headless)
        context = await browser.new_context()
        yield browser, context
        await context.close()
        await browser.close()

def browser_options(f):
    f = click.option('--username','-u', envvar='UULM_USERNAME', prompt='Enter your kiz username:')(f)
    f = click.option('--password','-p', envvar='UULM_PASSWORD', prompt='Enter your kiz password:', hide_input=True)(f)
    f = click.option('--headless', '-h', is_flag=True, help='Dont show the browser window')(f)
    return f

def fcfs_options(f):
    f = click.argument('target_times', nargs=-1, type=click.DateTime( ['%H:%M','%H:%M:%S']), required=True)(f)
    return f

@click.group()
@click.option('--debug', '-d', is_flag=True, help='Set the log level to DEBUG')
@click.option('--log-level', '-l', type=click.Choice(logging.getLevelNamesMapping().keys()),default = 'INFO')
async def cli(debug, log_level):
    '''
    Passing username and password is supported through multiple ways
    as entering your password visibly into your shell history is discouraged for security reasons. 

    \b
    - using environment variables `UULM_USERNAME`, `UULM_PASSWORD`
    - using a `.env` file in the current working directory with the same variables
    - interactive mode, if none of the above were specified
    
    \b
    For help concerning specific commands, run `uulm <COMMAND> --help`
    '''
    logging.basicConfig(level=log_level,format='%(asctime)s - %(levelname)s - %(message)s')
    if(debug): logger.setLevel(logging.DEBUG)

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

@cli.command()
@fcfs_options
@browser_options
@click.option('--offset', '-o', type=int, default=10, help='How many seconds before and after the target time to send')
async def coronang(target_times, username, password, headless, offset):
    '''
    Automatically register for courses on CoronaNG by specifying one or more timestamps of the format "HH:MM:SS".
    Please beware that CoronaNG only allows one active session at all times.
    '''
    CORONANG_VERSION='v1.8.00'
    CORONANG_URL="https://campusonline.uni-ulm.de/CoronaNG/user/mycorona.html"
    logger.debug('Parsed input times as %s', target_times)
    before_seconds = timedelta(seconds=offset)
    target_times = sorted(list(target_times))
    async for browser, context in run_playwright(headless):
        page = await context.new_page()
        loop = asyncio.get_event_loop()
        await page.goto(CORONANG_URL)
        server_version = await page.locator("css=#mblock_innen > a:nth-child(1)").inner_text()
        if(server_version != CORONANG_VERSION):
            logger.warning('Read CoronaNG version %s. Last tested version is %s. Please use --headful flag to ensure that everything is working.',
                           server_version, CORONANG_VERSION)

        # iterate over staggered login
        for target_time in target_times:
            # waiting loop for execution
            while True:
                server_str = await page.locator("css=#mblock_innen").inner_text()
                server_time = datetime.strptime(server_str.split().pop(), "%H:%M:%S")
                dtime = cast(timedelta, target_time -server_time )
                dtime_before = dtime - before_seconds
                logger.debug('Server Time: %s, delta: %s', server_time.time(), dtime_before)
                # window started?
                if dtime_before < timedelta(0):
                    time_start = loop.time()
                    time_prev = loop.time()
                    i = 0
                    # spamming loop
                    while True:
                        time_delta: float = loop.time() - time_prev
                        if time_delta > 1:
                            logger.info('%.2f requests per second sent', i / time_delta)
                            time_prev = loop.time()
                            i = 0 
                        # login necessary?
                        if (await page.locator("input[name=\"uid\"]").count()) >0:
                            logger.info('Logging in')
                            await page.locator("input[name=\"uid\"]").click()
                            await page.locator("input[name=\"uid\"]").fill(username)
                            await page.locator("input[name=\"password\"]").click()
                            await page.locator("input[name=\"password\"]").fill(password)
                            await page.get_by_role("button", name="Anmelden").click()
                            logger.info('Loading Overview Page')
                            await page.goto(CORONANG_URL)
                            await page.get_by_role("table", name="Ihre Beobachtungen. Sie kö").get_by_role("button").click()
                            await page.get_by_role("table", name="Ihre Beobachtungen. Sie kö").get_by_role("combobox").select_option("5")
                            await page.get_by_role("cell", name="An Markierten teilnehmen Ausf").get_by_role("button").click()
                            await page.reload()
                        # window ended?
                        # check window of offset before and after target
                        if loop.time() - 2 * offset > time_start:
                            break
                        # spam reload
                        # TODO set timeout, tweak
                        await page.reload()
                        i +=1
                    # after loop completion
                    logger.info('Iteration for time %s over', target_time.time())
                    break # out of waiting loop
                # not in time window?
                else:
                    await asyncio.sleep(1)
                    logger.info('Reloading to wait for event window in %s, %s before submission starts', dtime_before, dtime)
                    await page.reload()
    return

@cli.command()
@fcfs_options
@click.option('--target_course', '-t', multiple=True, required=True, help='Unique course name to register for. Can be passed multiple times')
@browser_options
@click.option('--offset', '-o', type=int, default=10, help='How many seconds before and after the target time to send')
async def sport(target_times, target_course, username, password, headless, offset):
    '''
    Automatically register for courses on the AktivKonzepte Hochschulsport Platform
    by specifying one or more timestamps of the format "HH:MM:SS".
    '''
    print(target_course)
    # TODO Check Version in HTML Head of Kursliste
    logger.debug('Parsed input times as %s', target_times)
    before_seconds = timedelta(seconds=offset)
    target_times = sorted(list(target_times))
    async for browser, context in run_playwright(headless):
        pages = [await context.new_page() for _ in target_course ]
        for course, page in zip(target_course, pages):
            await page.goto(course)
        await asyncio.sleep(20)
    return

@cli.command()
@click.argument('filename', type=click.Path(exists=True))
@click.option('--target_lp', '-t', type=int, default=74, help='Target number of n credits needed')
def grades(filename, target_lp:int):
    '''
    Calculate your weighted grade using the best n credits.
    Expects a csv with the columns "name, grade, credits".
    '''
    data = pd.read_csv(filename)
    data.sort_values(by='grade', inplace=True)

    acc_note: float = 0.0
    acc_lp = 0
    # the use of iterrows and all iteration over dataframes is discouraged for performance reasons
    for _ , row in data.iterrows():
        if acc_lp + row['credits'] < target_lp:
            weight = row['credits']
        else:
            weight = target_lp - acc_lp
            break
        acc_lp += weight
        acc_note = acc_note + weight * row['grade']
        logger.debug('Added "%s" with %d/%d credits and grade %.1f', row['name'], weight, row['credits'], row['grade'])
    acc_note: float = acc_note / acc_lp
    print(f'Final Grade: {acc_note:.2f} with {acc_lp}/{target_lp} credits')

if __name__ == "__main__":
    asyncio.run(cli.main())