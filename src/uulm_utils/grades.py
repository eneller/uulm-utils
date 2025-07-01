import asyncclick as click
import pandas as pd


from uulm_utils.common import cli, logger

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
