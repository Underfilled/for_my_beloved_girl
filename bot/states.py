from aiogram.fsm.state import State, StatesGroup


class UserState(StatesGroup):
    choosing_mode = State()
    roulette = State()
    dialog_searching = State()
    dialog_chatting = State()
