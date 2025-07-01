import asyncio

from uulm_utils.common import cli

import uulm_utils.campusonline
import uulm_utils.coronang
import uulm_utils.grades
import uulm_utils.sport

if __name__ == "__main__":
    asyncio.run(cli.main())