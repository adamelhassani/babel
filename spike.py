import asyncio

from babel import config, world
from babel.villager import Villager


async def main():
    objects = world.make_objects(colors=config.COLORS[:2], shapes=config.SHAPES, sizes=config.SIZES[:1])
    assert len(objects) == 6
    a = Villager("A", "spike", backend="B", seed=1)
    b = Villager("B", "spike", backend="B", seed=2)
    results = []
    invalid = 0
    for i in range(1, 41):
        speaker, listener = (a, b) if i % 2 else (b, a)
        game = await world.play_game(i, i, "spike", speaker, listener, objects=objects, max_len=3, noise=0.0, n_distractors=2)
        results.append(game.success)
        invalid += 0 if game.valid else 1
        if i % 5 == 0:
            rolling = sum(results[-10:]) / 10
            print(f"game {i}: heard={game.heard!r} valid={game.valid} success={game.success} rolling10={rolling:.2f}")
    total = sum(results) / len(results)
    print(f"final success={total:.2f} invalid={invalid}")
    if invalid == 0 and total >= 0.75:
        print("PHASE 0 PASS")
    else:
        print("PHASE 0 CHECK: spec wants invalid=0 and success passing 75% by game 40 (and not 100% by game 5)")


if __name__ == "__main__":
    asyncio.run(main())
