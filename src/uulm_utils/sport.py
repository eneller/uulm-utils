import asyncclick as click

import asyncio
from datetime import timedelta, datetime
from typing import cast

from uulm_utils.common import cli, fcfs_options, browser_options, run_playwright, logger

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
