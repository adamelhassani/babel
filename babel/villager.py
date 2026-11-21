import json
import random

from . import config, llm, world

SYLLABLE_LINE = " ".join(config.SYLLABLES)


def system_prompt(max_len, instinct):
    return (
        "You live in a village. You trade by naming objects to a partner.\n"
        f"You may ONLY use these syllables: {SYLLABLE_LINE}\n"
        f"A message is 1 to {max_len} syllables separated by spaces. Nothing else.\n"
        "You do not know any human language for this task. Do not base word choices on English spellings or sounds.\n"
        "You succeed when your partner picks the object you meant.\n"
        "Reuse what worked before. Change what failed. Shorter is better.\n"
        f"Your private instinct order for syllables: {' '.join(instinct)}\n"
        'Reply with JSON only: {"message": "..."} when speaking, {"choice": <index>} when listening.'
    )


class Villager:
    def __init__(self, name, village, model=None, backend=None, history_size=None, seed=None):
        self.name = name
        self.village = village
        self.model = model or config.MODEL
        self.backend = (backend or config.VILLAGER_BACKEND).upper()
        self.history_size = history_size or config.HISTORY_IN_PROMPT
        rng = random.Random(seed)
        self.instinct = config.SYLLABLES[:]
        rng.shuffle(self.instinct)
        self.history = []
        self.agent_id = None
        self.session_id = None

    def temperature(self, round_no):
        return 1.0 if round_no <= 10 else 0.5

    def history_text(self):
        lines = [
            f"message={g['message']} options={g['options']} choice={g['choice']} target={g['target']} success={g['success']}"
            for g in self.history[-self.history_size:]
        ]
        return "\n".join(lines) if lines else "(no games yet)"

    def options_text(self, options):
        return "\n".join(f"{i}: {o.label()}" for i, o in enumerate(options))

    async def _call(self, user_content, round_no, max_len=None):
        max_len = config.MAX_LEN if max_len is None else max_len
        if self.backend == "A":
            return await self._call_agent(user_content, max_len)
        messages = [
            {"role": "system", "content": system_prompt(max_len, self.instinct)},
            {"role": "user", "content": user_content + f"\nHistory:\n{self.history_text()}\nReply with JSON only."},
        ]
        return await llm.call_model_json(self.model, messages, temperature=self.temperature(round_no))

    async def _call_agent(self, user_content, max_len):
        client = llm.client()
        if self.agent_id is None:
            agent = await client.beta.agents.create_async(model=self.model, name=self.name, instructions=system_prompt(max_len, self.instinct))
            self.agent_id = agent.id
            session = await client.beta.conversations.start_async(agent_id=self.agent_id, inputs=user_content)
            self.session_id = session.conversation_id
            result = session
        else:
            result = await client.beta.conversations.append_async(conversation_id=self.session_id, inputs=user_content)
        content = result.outputs[-1].content if hasattr(result, "outputs") else result
        return json.loads(content)

    async def speak(self, target, options, round_no=1, max_len=None):
        data = await self._call(f"Target object: {target.label()}\nOptions:\n{self.options_text(options)}", round_no, max_len)
        return str(data.get("message", "")).strip()

    async def listen(self, message, options, round_no=1):
        data = await self._call(f"Message: {message}\nOptions:\n{self.options_text(options)}", round_no)
        try:
            return int(data.get("choice", -1))
        except (TypeError, ValueError):
            return -1

    async def name_objects(self):
        labels = [o.label() for o in world.OBJECTS]
        data = await self._call(
            "Name every object below with the word you use for it.\n" + "\n".join(labels)
            + '\nReply with JSON only: {"dict": {"<object>": "<word>"}}',
            round_no=999,
        )
        return data.get("dict", {})

    def learn(self, feedback):
        self.history.append(feedback)
        self.history = self.history[-self.history_size:]
