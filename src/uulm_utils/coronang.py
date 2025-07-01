import asyncclick as click

import asyncio
from datetime import timedelta, datetime
from typing import cast

from uulm_utils.common import cli, fcfs_options, browser_options, run_playwright, logger


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
