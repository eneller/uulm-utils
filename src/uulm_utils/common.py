import asyncclick as click
from dotenv import load_dotenv
from playwright.async_api import Page, async_playwright

import logging

load_dotenv()  # take environment variables
logger = logging.getLogger(__name__)

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

def browser_options(f):
    f = click.option('--username','-u', envvar='UULM_USERNAME', prompt='Enter your kiz username:')(f)
    f = click.option('--password','-p', envvar='UULM_PASSWORD', prompt='Enter your kiz password:', hide_input=True)(f)
    f = click.option('--headless', '-h', is_flag=True, help='Dont show the browser window')(f)
    return f

def fcfs_options(f):
    f = click.argument('target_times', nargs=-1, type=click.DateTime( ['%H:%M','%H:%M:%S']), required=True)(f)
    return f

async def run_playwright(headless: bool):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=headless)
        context = await browser.new_context()
        yield browser, context
        await context.close()
        await browser.close()
