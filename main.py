from enum import Enum
import asyncclick as click
import questionary
from playwright.async_api import async_playwright, Playwright

import re
import asyncio
from time import sleep


Selection = Enum('Selection', ['TREE_WALK', 'TREE_LEAF', 'ITEM_SELECTED'])

async def selection_or_walk(options):
    walkstr = 'Walk the Tree from here'
    options = [questionary.Choice(title=walkstr, checked=True)] + [questionary.Choice(opt.strip()) for opt in options]
    selection = await questionary.select(choices=options, message='Select one of the following options').ask_async()
    if selection == walkstr: return Selection.TREE_WALK , None
    return Selection.ITEM_SELECTED, selection

@click.group()
@click.option('--username','-u')
@click.option('--password','-p')
@click.option('--headful', is_flag=True)
@click.pass_context
async def cli(ctx, username, password, headful):
    ctx.ensure_object(dict)
    ctx.obj['USERNAME'] = username
    ctx.obj['PASSWORD'] = password
    ctx.obj['HEADLESS'] = not headful

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=headful)
        context = await browser.new_context()
        page = await context.new_page()
        ctx.obj['PAGE'] = page
        yield  # Subcommands run here
        await page.close()
        await context.close()
        await browser.close()

@cli.command()
@click.pass_context
async def campusonline(ctx):
    username = ctx.obj['USERNAME']
    password = ctx.obj['PASSWORD']
    page = ctx.obj['PAGE']
    click.echo("Running campusonline...")
    await page.goto("https://campusonline.uni-ulm.de")
    await page.get_by_role("textbox", name="Benutzerkennung").click()
    await page.get_by_role("textbox", name="Benutzerkennung").fill(username)
    await page.get_by_role("textbox", name="Passwort").fill(password)
    await page.get_by_role("button", name="Anmelden").click()
    await page.get_by_role("link", name="Studium").click()
    await page.get_by_role("link", name="Modulbeschreibungen ansehen").click()
    options = await page.locator('css=li.treelist').all_inner_texts()
    selection = await selection_or_walk(options)
    print(selection)
    sleep(2)
    click.echo("Finished campusonline.")

@cli.command()
@click.pass_context
async def coronang(ctx):
    username = ctx.obj['USERNAME']
    password = ctx.obj['PASSWORD']
    page = ctx.obj['PAGE']
    click.echo("Running coronang...")
    await page.goto("https://campusonline.uni-ulm.de/CoronaNG/user/mycorona.html")
    await page.locator("input[name=\"uid\"]").click()
    await page.locator("input[name=\"uid\"]").fill(username)
    await page.locator("input[name=\"password\"]").click()
    await page.locator("input[name=\"password\"]").fill(password)
    await page.get_by_role("button", name="Anmelden").click()
    await page.get_by_role("link", name="Beobachtungen & Teilnahmen").click()
    await page.get_by_role("table", name="Ihre Beobachtungen. Sie kö").get_by_role("button").click()
    await page.get_by_role("table", name="Ihre Beobachtungen. Sie kö").get_by_role("combobox").select_option("5")
    await page.get_by_role("cell", name="An Markierten teilnehmen Ausf").get_by_role("button").click()
    await page.reload()
    click.echo("Finished coronang.")

if __name__ == "__main__":
    asyncio.run(cli.main())