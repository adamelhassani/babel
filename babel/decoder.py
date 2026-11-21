import random

from . import config, llm

PROMPT = (
    "You are an outside observer. You do NOT know which object was the target in past games, "
    "but you saw each message, the options, which option was chosen, and whether it succeeded.\n"
    "Learn the invented language from the examples, then predict the target object for each held-out game.\n"
    'Reply with JSON only: {"choices": [<index>, ...]} with one index per held-out game.'
)


def games_to_text(games):
    return "\n".join(f"message={g.heard} options={g.options} choice={g.choice} success={g.success}" for g in games)


async def decoder_accuracy(village_games, model=None, seed=0):
    model = model or config.MODEL
    valid = [g for g in village_games if g.valid]
    if len(valid) < config.DECODER_HISTORY + config.DECODER_HOLDOUT:
        return 0.0
    rng = random.Random(seed)
    recent = valid[-config.DECODER_HISTORY:]
    holdout = rng.sample(valid[:-config.DECODER_HISTORY], config.DECODER_HOLDOUT)
    user = (
        f"Past games:\n{games_to_text(recent)}\n\nHeld-out games (message + options only):\n"
        + "\n".join(f"{i}: message={g.heard} options={g.options}" for i, g in enumerate(holdout))
        + "\nReply with JSON only."
    )
    data = await llm.call_model_json(model, [{"role": "system", "content": PROMPT}, {"role": "user", "content": user}], temperature=0.0)
    choices = data.get("choices", [])
    correct = 0
    for i, g in enumerate(holdout):
        if i < len(choices):
            try:
                if int(choices[i]) == g.options.index(g.target):
                    correct += 1
            except (TypeError, ValueError):
                pass
    return correct / len(holdout)
