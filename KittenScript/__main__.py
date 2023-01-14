import click

from .ide import IDE
from .ide_cn import IDE_CN
from .version import get_version
from .stdio import interpreter_file, interpreter_stdin


def show_version(ctx, _, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(get_version())
    ctx.exit()
    
    
def run_ide(ctx, _, value):
    if not value or ctx.resilient_parsing:
        return
    ide = IDE()
    ide.show()
    ctx.exit()
    

def run_ide_cn(ctx, _, value):
    if not value or ctx.resilient_parsing:
        return
    ide = IDE_CN()
    ide.show()
    ctx.exit()
    
    
def enter_ip(ctx, _, value):
    if not value or ctx.resilient_parsing:
        return
    interpreter_stdin()
    ctx.exit()


@click.command()
@click.option('-v', '--version', is_flag=True, callback=show_version,
              expose_value=False, help='Show the version and exit.')
@click.option('-i', '--ide', is_flag=True, callback=run_ide,
              expose_value=False, help='Show the IDE in English and exit.')
@click.option('-ic', '--ide-cn', is_flag=True, callback=run_ide_cn,
              expose_value=False, help='Show the IDE in Chinese and exit.')
@click.option('-s', '--stdio', is_flag=True, callback=enter_ip,
              expose_value=False, help='Enter interactive programming.')
@click.argument('file', nargs=1)
def main(file):
    if file == 'stdin':
        interpreter_stdin()
    else:
        interpreter_file(file)


if __name__ == '__main__':
    main()
