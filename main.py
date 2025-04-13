import asyncclick as click
import questionary
from playwright.async_api import async_playwright, Playwright

import re
import asyncio
from time import sleep

async def run(
        playwright: Playwright,
        username,
        password,
        headless:bool,
        ) -> None:
    if not username: username = await questionary.text('Enter your kiz username:').ask_async()
    if not password: password = await questionary.password('Enter your kiz password:').ask_async()
    browser = await playwright.chromium.launch(headless=headless)
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto("https://campusonline.uni-ulm.de")
    await page.get_by_role("textbox", name="Benutzerkennung").click()
    await page.get_by_role("textbox", name="Benutzerkennung").fill("dkp11")
    await page.get_by_role("textbox", name="Passwort").fill("zy7Av5rickeyyy")
    await page.get_by_role("button", name="Anmelden").click()
    await page.get_by_role("link", name="Studium").click()
    await page.get_by_role("link", name="Modulbeschreibungen ansehen").click()
    await page.get_by_text("Modulbeschreibungen Bitte wä").click()
    await page.get_by_role("link", name="Module für Abschluss: Master of Science").click()
    await page.get_by_text("Modulbeschreibungen Sie").click()
    await page.get_by_role("link", name="Studiengang: Informatik").click()
    await page.get_by_role("link", name="Studium gemäß Prüfungsordnung: 2022").click()
    await page.get_by_role("link", name="Wahlpflichtbereich").click()
    await page.get_by_role("link", name="Kernbereich Informatik").click()
    await page.get_by_role("link", name="Kernbereich Praktische").click()
    await page.get_by_role("link", name="Data Mining").click()
    await page.get_by_role("link", name="Beschreibung anzeigen").click()
    sleep(20)
    await page.close()

    # ---------------------
    await context.close()
    await browser.close()

@click.command()
@click.option('--username','-u')
@click.option('--password','-p')
async def main(username, password):
    async with async_playwright() as playwright:
        await run(playwright, username, password, True)

if __name__ == "__main__":
    asyncio.run(main())