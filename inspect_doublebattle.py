import inspect
from poke_env.battle.double_battle import DoubleBattle

members = [n for n in dir(DoubleBattle) if 'mega' in n.lower() or 'available' in n.lower() or n.startswith('can_')]
print('Filtered members:')
for m in members:
    print(m)

print('\nSource available?')
try:
    src = inspect.getsource(DoubleBattle)
    lines = src.splitlines()
    print('\n'.join(lines[:400]))
except Exception as e:
    print('Error getting source:', e)
