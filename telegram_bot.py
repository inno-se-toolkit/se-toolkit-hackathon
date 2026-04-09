from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from database import init_db, get_question_by_number, get_all_questions

BOT_TOKEN = "6028803238:AAFOKriRYI3XgTeRFMNJiB7quKw1QWN4Cu8"

TOTAL_QUESTIONS = 100

# Хранилище состояний пользователей: {user_id: {"current_question": int, "answers": {}}}
user_sessions: dict[int, dict] = {}


def _get_rating_keyboard() -> ReplyKeyboardMarkup:
    """Формирует фиксированную клавиатуру с оценками 1–5."""
    buttons = [["1", "2", "3", "4", "5"]]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def _get_start_keyboard() -> ReplyKeyboardMarkup:
    """Формирует стартовую клавиатуру с доступными командами."""
    buttons = [["/test"], ["/results"], ["/help"]]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start — приветствие и список команд."""
    text = (
        "👋 Добро пожаловать в бот для психологического тестирования!\n\n"
        "Этот бот поможет вам пройти опросник из 100 вопросов и узнать больше о себе.\n\n"
        "📋 Доступные команды:\n"
        "/test — начать или продолжить тест\n"
        "/results — посмотреть текущие результаты\n"
        "/help — справка по боту\n\n"
        "Готовы начать? Отправьте /test!"
    )
    await update.message.reply_text(
        text, reply_markup=_get_start_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help."""
    text = (
        "📖 Справка\n\n"
        "Бот проведёт вас через 100 вопросов, охватывающих 8 блоков:\n"
        "1. Темперамент\n"
        "2. Характер\n"
        "3. Ценности и убеждения\n"
        "4. Эмоциональная сфера\n"
        "5. Когнитивные особенности\n"
        "6. Способности и одарённость\n"
        "7. Мотивация и направленность\n"
        "8. Самосознание и самооценка\n\n"
        "На каждый вопрос ответьте числом от 1 до 5:\n"
        "1 — совсем не согласен\n"
        "2 — скорее не согласен\n"
        "3 — затрудняюсь ответить\n"
        "4 — скорее согласен\n"
        "5 — полностью согласен\n\n"
        "Команды:\n"
        "/start — главное меню\n"
        "/test — начать / продолжить тест\n"
        "/results — текущие результаты"
    )
    await update.message.reply_text(text, reply_markup=_get_start_keyboard())


async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /test — начинает тест или продолжает с последнего вопроса."""
    user_id = update.effective_user.id

    if user_id not in user_sessions:
        user_sessions[user_id] = {"current_question": 1, "answers": {}}

    session = user_sessions[user_id]
    question_number = session["current_question"]

    if question_number > TOTAL_QUESTIONS:
        await update.message.reply_text(
            "🎉 Вы уже прошли все 100 вопросов! Используйте /results для просмотра результатов.",
            reply_markup=_get_start_keyboard(),
        )
        return

    question = get_question_by_number(question_number)
    if not question:
        await update.message.reply_text(
            f"❌ Вопрос #{question_number} не найден в базе данных.",
            reply_markup=_get_start_keyboard(),
        )
        return

    text = (
        f"📝 Вопрос {question_number} из {TOTAL_QUESTIONS}\n"
        f"📂 Категория: {question['category']}\n\n"
        f"{question['text']}"
    )
    await update.message.reply_text(
        text, reply_markup=_get_rating_keyboard()
    )


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ответ пользователя и переходит к следующему вопросу."""
    user_id = update.effective_user.id
    answer_text = update.message.text.strip()

    if user_id not in user_sessions:
        await update.message.reply_text(
            "Сначала начните тест командой /test.",
            reply_markup=_get_start_keyboard(),
        )
        return

    session = user_sessions[user_id]
    question_number = session["current_question"]

    if answer_text not in ("1", "2", "3", "4", "5"):
        await update.message.reply_text(
            "Пожалуйста, выберите число от 1 до 5 с помощью клавиатуры.",
            reply_markup=_get_rating_keyboard(),
        )
        return

    session["answers"][question_number] = int(answer_text)
    session["current_question"] += 1

    if session["current_question"] > TOTAL_QUESTIONS:
        await update.message.reply_text(
            "🎉 Поздравляем! Вы завершили все 100 вопросов!\n\n"
            "Используйте /results для просмотра результатов.",
            reply_markup=_get_start_keyboard(),
        )
        return

    question = get_question_by_number(session["current_question"])
    text = (
        f"✅ Принято.\n\n"
        f"📝 Вопрос {session['current_question']} из {TOTAL_QUESTIONS}\n"
        f"📂 Категория: {question['category']}\n\n"
        f"{question['text']}"
    )
    await update.message.reply_text(
        text, reply_markup=_get_rating_keyboard()
    )


async def results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /results — показывает текущие результаты."""
    user_id = update.effective_user.id

    if user_id not in user_sessions or not user_sessions[user_id]["answers"]:
        await update.message.reply_text(
            "Вы ещё не ответили ни на один вопрос. Начните тест командой /test.",
            reply_markup=_get_start_keyboard(),
        )
        return

    session = user_sessions[user_id]
    answers = session["answers"]
    answered = len(answers)

    text = f"📊 Ваши результаты\n\nОтвечено вопросов: {answered} из {TOTAL_QUESTIONS}\n\n"

    # Группировка по категориям
    categories: dict[str, list[int]] = {}
    for q_num, score in answers.items():
        q = get_question_by_number(q_num)
        if q:
            cat = q["category"]
            categories.setdefault(cat, []).append(score)

    for cat, scores in categories.items():
        avg = sum(scores) / len(scores)
        text += f"📂 {cat}: средний балл {avg:.2f} ({len(scores)} вопр.)\n"

    await update.message.reply_text(text, reply_markup=_get_start_keyboard())


def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("test", test_command))
    app.add_handler(CommandHandler("results", results))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))
    app.run_polling()


if __name__ == "__main__":
    main()
