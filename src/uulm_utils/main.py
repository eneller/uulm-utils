import asyncclick as click
import questionary
from playwright.async_api import async_playwright, Playwright
import pandas as pd

from enum import Enum
import asyncio
from time import sleep
import logging


logger = logging.getLogger(__name__)

CORONANG_VERSION='v1.8.00'
Selection = Enum('Selection', ['TREE_WALK', 'TREE_LEAF', 'ITEM_SELECTED'])

async def selection_or_walk(options):
    walkstr = 'Walk the Tree from here'
    options = [questionary.Choice(title=walkstr, checked=True)] + [questionary.Choice(opt.strip()) for opt in options]
    selection = await questionary.select(choices=options, message='Select one of the following options').ask_async()
    if selection == walkstr: return Selection.TREE_WALK , None
    return Selection.ITEM_SELECTED, selection

async def run_playwright(headless: bool):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=headless)
        context = await browser.new_context()
        page = await context.new_page()
        yield page, browser, context
        await page.close()
        await context.close()
        await browser.close()

@click.group()
@click.option('--username','-u')
@click.option('--password','-p')
@click.option('--headful', is_flag=True, help='Show the browser window')
@click.option('--debug', '-d', is_flag=True, help='Set the log level to DEBUG')
@click.pass_context
async def cli(ctx, username, password, headful, debug):
    logging.basicConfig(level=logging.WARNING,format='%(asctime)s - %(levelname)s - %(message)s')
    if(debug): logger.setLevel(logging.DEBUG)
    ctx.ensure_object(dict)
    if ctx.invoked_subcommand != 'grades':
        ctx.obj['USERNAME'] = username or await questionary.text('Enter your kiz username:').ask_async()
        ctx.obj['PASSWORD'] = password or await questionary.password('Enter your kiz password:').ask_async()
        ctx.obj['HEADLESS'] = not headful

@cli.command(help='Interact with the module tree in Campusonline')
@click.pass_context
async def campusonline(ctx):
    async for page, browser, context in run_playwright(ctx.obj['HEADLESS']):
        click.echo("Running campusonline...")
        await page.goto("https://campusonline.uni-ulm.de")
        await page.get_by_role("textbox", name="Benutzerkennung").click()
        await page.get_by_role("textbox", name="Benutzerkennung").fill(ctx.obj['USERNAME'])
        await page.get_by_role("textbox", name="Passwort").fill(ctx.obj['PASSWORD'])
        await page.get_by_role("button", name="Anmelden").click()
        await page.get_by_role("link", name="Studium").click()
        await page.get_by_role("link", name="Modulbeschreibungen ansehen").click()
        options = await page.locator('css=li.treelist').all_inner_texts()
        selection = await selection_or_walk(options)
        print(selection)
        sleep(2)
        click.echo("Finished campusonline.")

@cli.command(help='Automatically register for courses on CoronaNG')
@click.pass_context
async def coronang(ctx):
    async for page, browser, context in run_playwright(ctx.obj['HEADLESS']):
        click.echo("Running coronang...")
        await page.goto("https://campusonline.uni-ulm.de/CoronaNG/user/mycorona.html")
        version = await page.locator("css=#mblock_innen > a:nth-child(1)").inner_text()
        if(version != CORONANG_VERSION):
            logger.warning('Read CoronaNG version %s. Last tested version is %s. Please use --headful flag to ensure that everything is working.',
                           version, CORONANG_VERSION)
        await page.locator("input[name=\"uid\"]").click()
        await page.locator("input[name=\"uid\"]").fill(ctx.obj['USERNAME'])
        await page.locator("input[name=\"password\"]").click()
        await page.locator("input[name=\"password\"]").fill(ctx.obj['PASSWORD'])
        await page.get_by_role("button", name="Anmelden").click()
        await page.get_by_role("link", name="Beobachtungen & Teilnahmen").click()
        await page.get_by_role("table", name="Ihre Beobachtungen. Sie kö").get_by_role("button").click()
        await page.get_by_role("table", name="Ihre Beobachtungen. Sie kö").get_by_role("combobox").select_option("5")
        await page.get_by_role("cell", name="An Markierten teilnehmen Ausf").get_by_role("button").click()
        await page.reload()
        click.echo("Finished coronang.")

@cli.command(help='''Calculate your weighted grade using the best n credits. Expects a csv with the columns name, grade, credits''')
@click.argument('filename', type=click.Path(exists=True))
@click.option('--target_lp', '-t', type=int, default=74, help='Target number of n credits needed')
def grades(filename, target_lp:int):
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
    print(f'Final Grade: {acc_note}')

if __name__ == "__main__":
    asyncio.run(cli.main())