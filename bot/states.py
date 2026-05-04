from aiogram.fsm.state import State, StatesGroup


class UserState(StatesGroup):
    main_menu = State()
    choosing_category = State()
    recording_whisper = State()
    listening = State()
    whisper_back = State()
    inbox = State()
