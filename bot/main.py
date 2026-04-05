"""Main bot application - single ConversationHandler architecture"""

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from bot.data.car_config_data import CARS, ENGINES, SUSPENSIONS, BODYKITS, WHEELS
from bot.data.storage import save_order, get_all_orders, get_order, update_order_status, get_order_stats

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
(
    MAIN_MENU,
    # Config states
    SELECT_CAR, SELECT_ENGINE, SELECT_SUSPENSION, SELECT_BODYKIT, SELECT_WHEEL, CONFIG_SUMMARY,
    # Order states
    ORDER_REVIEW, ORDER_CONFIRMED,
    # Admin states
    ADMIN_AUTH, ADMIN_MENU, ADMIN_ORDER_LIST, ADMIN_ORDER_DETAIL,
) = range(13)

# Admin settings
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'service2024')

# Status display
STATUS_NAMES = {
    'new': '🆕 Новый',
    'in_progress': '🔧 В работе',
    'completed': '✅ Выполнен',
    'cancelled': '❌ Отменён',
}
STATUS_EMOJI = {
    'new': '🆕',
    'in_progress': '🔧',
    'completed': '✅',
    'cancelled': '❌',
}


# ==================== Helpers ====================

def _main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚗 Конфигуратор", callback_data="menu_config")],
        [InlineKeyboardButton("📋 Мои заказы", callback_data="menu_orders")],
        [InlineKeyboardButton("🔧 Панель сервиса", callback_data="menu_admin")],
        [InlineKeyboardButton("ℹ️ О сервисе", callback_data="menu_about")],
    ])


async def show_main_menu(update: Update) -> int:
    """Show main menu screen"""
    text = (
        f"👋 Привет, {update.effective_user.first_name}!\n\n"
        f"🏎️ <b>JDM Config Bot</b> — сервис для заказа автомобилей из 90-х и 00-х с индивидуальной настройкой\n\n"
        f"Выберите действие:"
    )
    if update.message:
        await update.message.reply_text(text, parse_mode='HTML', reply_markup=_main_menu_keyboard())
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode='HTML', reply_markup=_main_menu_keyboard())
    return MAIN_MENU


async def _edit(update: Update, text: str, **kwargs):
    """Edit message or reply"""
    if update.callback_query:
        await update.callback_query.edit_message_text(text, **kwargs)
    elif update.effective_message:
        await update.effective_message.reply_text(text, **kwargs)


# ==================== Main Menu ====================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await show_main_menu(update)


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "menu_about":
        await query.edit_message_text(
            "ℹ️ <b>О сервисе</b>\n\n"
            "Мы помогаем заказать автомобили из 90-х и 00-х с индивидуальной настройкой:\n\n"
            "• Подбор двигателя и тюнинга\n"
            "• Настройка подвески\n"
            "• Установка обвесов\n"
            "• Подбор колёсных дисков\n\n"
            "Все работы выполняются профессиональными мастерами с опытом работы с JDM автомобилями."
            "\n\n📞 Для связи с менеджером: @manager_username",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]])
        )
        return MAIN_MENU

    elif data == "menu_config":
        return await start_config(update, context)

    elif data == "menu_orders":
        return await start_orders(update, context)

    elif data == "menu_admin":
        return await start_admin(update, context)

    elif data == "back_to_main":
        return await show_main_menu(update)

    return MAIN_MENU


# ==================== Config Flow ====================

async def start_config(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['config'] = {}
    keyboard = [[InlineKeyboardButton(f"{c['name']} ({c['years']})", callback_data=f"car_{c['id']}")] for c in CARS]
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")])
    await update.callback_query.edit_message_text(
        "🚗 <b>Конфигуратор автомобиля</b>\n\nВыберите автомобиль:",
        parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_CAR


async def select_car(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    car_id = query.data.replace("car_", "")
    car = next((c for c in CARS if c['id'] == car_id), None)
    if not car:
        return SELECT_CAR
    context.user_data['config']['car'] = car
    engines = ENGINES.get(car_id, [])
    keyboard = [[InlineKeyboardButton(e['name'], callback_data=f"engine_{e['id']}")] for e in engines]
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_config_car")])
    await query.edit_message_text(
        f"🚗 <b>{car['name']}</b>\nГоды: {car['years']}\n{car['description']}\n\n⚙️ Выберите двигатель:",
        parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_ENGINE


async def select_engine(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    engine_id = query.data.replace("engine_", "")
    car_id = context.user_data['config']['car']['id']
    engine = next((e for e in ENGINES.get(car_id, []) if e['id'] == engine_id), None)
    if not engine:
        return SELECT_ENGINE
    context.user_data['config']['engine'] = engine
    keyboard = [[InlineKeyboardButton(s['name'], callback_data=f"susp_{sid}")] for sid, s in SUSPENSIONS.items()]
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_config_engine")])
    await query.edit_message_text(
        f"⚙️ <b>{engine['name']}</b>\nМощность: {engine['power']}\n{engine['description']}\n\n🔧 Выберите подвеску:",
        parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_SUSPENSION


async def select_suspension(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    sid = query.data.replace("susp_", "")
    susp = SUSPENSIONS.get(sid)
    if not susp:
        return SELECT_SUSPENSION
    context.user_data['config']['suspension'] = {'id': sid, **susp}
    keyboard = [[InlineKeyboardButton(bk['name'], callback_data=f"bodykit_{bk['id']}")] for bk in BODYKITS]
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_config_susp")])
    await query.edit_message_text(
        f"🔧 <b>{susp['name']}</b>\n{susp['description']}\n"
        f"Клиренс: {susp['ride_height']} | Развал: {susp['camber']}\n\n🎨 Выберите обвес:",
        parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_BODYKIT


async def select_bodykit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    bk_id = query.data.replace("bodykit_", "")
    bk = next((b for b in BODYKITS if b['id'] == bk_id), None)
    if not bk:
        return SELECT_BODYKIT
    context.user_data['config']['bodykit'] = bk
    keyboard = []
    for i in range(0, len(WHEELS), 2):
        row = [InlineKeyboardButton(WHEELS[i]['name'], callback_data=f"wheel_{WHEELS[i]['id']}")]
        if i + 1 < len(WHEELS):
            row.append(InlineKeyboardButton(WHEELS[i+1]['name'], callback_data=f"wheel_{WHEELS[i+1]['id']}"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_config_bodykit")])
    components = "\n".join([f"• {c}" for c in bk['components']])
    await query.edit_message_text(
        f"🎨 <b>{bk['name']}</b>\n{bk['description']}\nСтиль: {bk['style']}\n\n"
        f"Компоненты:\n{components}\n\n🛞 Выберите диски:",
        parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_WHEEL


async def select_wheel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    w_id = query.data.replace("wheel_", "")
    wheel = next((w for w in WHEELS if w['id'] == w_id), None)
    if not wheel:
        return SELECT_WHEEL
    context.user_data['config']['wheels'] = wheel
    cfg = context.user_data['config']
    text = (
        f"✅ <b>Конфигурация готова!</b>\n\n"
        f"🚗 {cfg['car']['name']} ({cfg['car']['years']})\n"
        f"⚙️ {cfg['engine']['name']} — {cfg['engine']['power']}\n"
        f"🔧 {cfg['suspension']['name']}\n"
        f"🎨 {cfg['bodykit']['name']}\n"
        f"🛞 {cfg['wheels']['name']}\n"
    )
    keyboard = [
        [InlineKeyboardButton("📦 Оформить заказ", callback_data="place_order")],
        [InlineKeyboardButton("🔄 Начать заново", callback_data="restart_config")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")],
    ]
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIG_SUMMARY


async def config_summary_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "place_order":
        return await start_orders(update, context)
    elif query.data == "restart_config":
        return await start_config(update, context)
    return CONFIG_SUMMARY


# ==================== Order Flow ====================

async def start_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    config = context.user_data.get('config', {})
    user_id = update.effective_user.id
    all_orders_list = get_all_orders()
    my_orders = [o for o in all_orders_list if o.get('user_id') == user_id]

    if my_orders:
        text = f"📋 <b>Ваши заказы ({len(my_orders)})</b>\n\n"
        for o in my_orders[:10]:
            car = o.get('car', {}).get('name', 'N/A')
            st = o.get('status', 'new')
            text += f"{STATUS_EMOJI.get(st, '📋')} <code>{o['id']}</code> — {car}\n"
            text += f"   Статус: {STATUS_NAMES.get(st, st)} | {o.get('created_at', '')}\n\n"
    else:
        text = "📋 <b>У вас пока нет заказов</b>\n\n"

    if config:
        keyboard = [
            [InlineKeyboardButton("📦 Оформить заказ", callback_data="confirm_order")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")],
        ]
    else:
        text += "Сначала настройте автомобиль через Конфигуратор."
        keyboard = [
            [InlineKeyboardButton("🚗 Конфигуратор", callback_data="menu_config")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")],
        ]
    await _edit(update, text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
    return ORDER_REVIEW


async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    cfg = context.user_data.get('config', {})
    if not cfg:
        await query.edit_message_text("❌ Нет конфигурации. Настройте автомобиль через Конфигуратор.")
        return MAIN_MENU

    order_data = {
        'user_id': query.from_user.id,
        'username': query.from_user.username or query.from_user.first_name,
        'car': cfg.get('car', {}), 'engine': cfg.get('engine', {}),
        'suspension': cfg.get('suspension', {}), 'bodykit': cfg.get('bodykit', {}),
        'wheels': cfg.get('wheels', {}), 'notes': '',
    }
    saved = save_order(order_data)
    text = (
        f"✅ <b>Заказ #{saved['id']} оформлен!</b>\n\n"
        f"🚗 {cfg['car']['name']} ({cfg['car']['years']})\n"
        f"⚙️ {cfg['engine']['name']} — {cfg['engine']['power']}\n"
        f"🔧 {cfg['suspension']['name']}\n"
        f"🎨 {cfg['bodykit']['name']}\n"
        f"🛞 {cfg['wheels']['name']}\n\n"
        f"Статус: 🆕 Новый\n"
        f"Скоро свяжется менеджер. Спасибо! 🚗"
    )
    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")]]
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
    context.user_data.pop('config', None)
    return ORDER_CONFIRMED


# ==================== Admin Flow ====================

async def start_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = "🔐 <b>Вход в панель сервиса</b>\n\nВведите пароль:"
    await _edit(update, text, parse_mode='HTML')
    return ADMIN_AUTH


async def handle_auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pwd = update.message.text if update.message else ""
    if pwd == ADMIN_PASSWORD:
        context.user_data['is_admin'] = True
        return await show_admin_menu(update)
    await update.message.reply_text("❌ Неверный пароль. Попробуйте снова:", parse_mode='HTML')
    return ADMIN_AUTH


async def show_admin_menu(update: Update) -> int:
    stats = get_order_stats()
    text = (
        f"🔧 <b>Панель сервиса</b>\n\n"
        f"📊 Всего: {stats['total']} | 🆕 {stats['new']} | 🔧 {stats['in_progress']} | ✅ {stats['completed']} | ❌ {stats['cancelled']}"
    )
    kb = [
        [InlineKeyboardButton("📋 Все заказы", callback_data="admin_all_orders")],
        [InlineKeyboardButton("🆕 Новые", callback_data="admin_new_orders")],
        [InlineKeyboardButton("🔧 В работе", callback_data="admin_progress_orders")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")],
    ]
    await _edit(update, text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(kb))
    return ADMIN_MENU


async def admin_menu_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    d = query.data

    if d in ("admin_all_orders", "admin_new_orders", "admin_progress_orders"):
        status = None
        if d == "admin_new_orders":
            status = 'new'
        elif d == "admin_progress_orders":
            status = 'in_progress'
        return await show_order_list(update, context, status)
    elif d == "admin_stats":
        return await show_admin_stats(update)
    elif d == "admin_back_menu":
        return await show_admin_menu(update)
    elif d == "admin_back_to_list":
        return await show_order_list(update, context)
    return ADMIN_MENU


async def show_order_list(update: Update, context: ContextTypes.DEFAULT_TYPE, status=None) -> int:
    orders = get_all_orders(status=status)
    if not orders:
        text = "📋 Заказов нет."
        kb = [[InlineKeyboardButton("⬅️ Назад", callback_data="admin_back_menu"), InlineKeyboardButton("🏠 Меню", callback_data="back_to_main")]]
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
        return ADMIN_ORDER_LIST

    text = f"📋 <b>Заказы ({len(orders)})</b>\n\n"
    for o in orders[:10]:
        car = o.get('car', {}).get('name', 'N/A')
        st = o.get('status', 'new')
        text += f"{STATUS_EMOJI.get(st,'📋')} <code>{o['id']}</code> — {car} | {o.get('username','?')} | {o.get('created_at','')}\n"
    if len(orders) > 10:
        text += f"\n...и ещё {len(orders) - 10}"

    kb = []
    for o in orders[:5]:
        car = o.get('car', {}).get('name', 'N/A')[:25]
        kb.append([InlineKeyboardButton(f"{STATUS_EMOJI.get(o.get('status','new'),'')} {o['id']} — {car}", callback_data=f"admin_order_{o['id']}")])
    kb.append([InlineKeyboardButton("⬅️ Назад", callback_data="admin_back_menu")])
    kb.append([InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")])
    if status:
        kb.insert(0, [InlineKeyboardButton("📋 Все заказы", callback_data="admin_all_orders")])

    await update.callback_query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(kb))
    return ADMIN_ORDER_LIST


async def show_order_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id) -> int:
    o = get_order(order_id)
    if not o:
        await update.callback_query.edit_message_text("❌ Заказ не найден")
        return ADMIN_ORDER_LIST

    car = o.get('car', {})
    text = (
        f"📦 <b>Заказ {o['id']}</b> | {STATUS_NAMES.get(o.get('status','new'),'')}\n"
        f"Создан: {o.get('created_at','')}\n\n"
        f"👤 {o.get('username','?')} (ID: {o.get('user_id','')})\n\n"
        f"🚗 {car.get('name','N/A')} ({car.get('years','')})\n"
        f"⚙️ {o.get('engine',{}).get('name','N/A')} — {o.get('engine',{}).get('power','')}\n"
        f"🔧 {o.get('suspension',{}).get('name','N/A')}\n"
        f"🎨 {o.get('bodykit',{}).get('name','N/A')}\n"
        f"🛞 {o.get('wheels',{}).get('name','N/A')}\n"
    )
    if o.get('notes'):
        text += f"\n📝 {o['notes']}\n"

    kb = []
    cur = o.get('status', 'new')
    for ns in ['new', 'in_progress', 'completed', 'cancelled']:
        if ns != cur:
            kb.append([InlineKeyboardButton(f"🔄 {STATUS_NAMES[ns]}", callback_data=f"admin_set_status_{o['id']}_{ns}")])
    kb.append([InlineKeyboardButton("⬅️ Назад", callback_data="admin_back_to_list")])
    kb.append([InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")])

    await update.callback_query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(kb))
    return ADMIN_ORDER_DETAIL


async def handle_order_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    d = query.data

    if d.startswith("admin_order_"):
        oid = d[len("admin_order_"):]
        return await show_order_detail(update, context, oid)

    if d.startswith("admin_set_status_"):
        data = d[len("admin_set_status_"):]
        parts = data.split('_')
        oid = parts[0]
        ns = '_'.join(parts[1:])
        o = update_order_status(oid, ns)
        if o:
            await query.edit_message_text(f"✅ Статус {oid} → {STATUS_NAMES.get(ns, ns)}")
            return await show_order_detail(update, context, oid)
        await query.edit_message_text("❌ Заказ не найден")
        return ADMIN_ORDER_LIST

    return ADMIN_ORDER_DETAIL


async def show_admin_stats(update: Update) -> int:
    stats = get_order_stats()
    orders = get_all_orders()
    cc = {}
    for o in orders:
        n = o.get('car', {}).get('name', 'N/A')
        cc[n] = cc.get(n, 0) + 1
    top = sorted(cc.items(), key=lambda x: x[1], reverse=True)[:5]
    top_text = "\n".join(f"   {i+1}. {n}: {c}" for i, (n, c) in enumerate(top)) or "   Нет данных"
    conv = f"({stats['completed']/stats['total']*100:.1f}%)" if stats['total'] > 0 else "(нет заказов)"
    text = (
        f"📊 <b>Статистика</b>\n\n"
        f"Всего: {stats['total']}\n"
        f"🆕 {stats['new']} | 🔧 {stats['in_progress']} | ✅ {stats['completed']} | ❌ {stats['cancelled']}\n\n"
        f"<b>Популярные авто:</b>\n{top_text}\n\n"
        f"<b>Конверсия:</b> {stats['completed']}/{stats['total']} {conv}"
    )
    kb = [
        [InlineKeyboardButton("⬅️ Назад", callback_data="admin_back_menu")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")],
    ]
    await update.callback_query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(kb))
    return ADMIN_MENU


# ==================== Back to Main ====================

async def back_to_main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await show_main_menu(update)


# ==================== Bot Setup ====================

def main():
    """Start the bot"""
    token = os.getenv('BOT_TOKEN')
    if not token:
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        if k.strip() == 'BOT_TOKEN':
                            token = v.strip()
                            break
    if not token:
        logger.error("BOT_TOKEN not found")
        return

    app = ApplicationBuilder().token(token).build()

    # Single ConversationHandler for everything
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(menu_handler, pattern='^menu_'),
                CallbackQueryHandler(back_to_main_handler, pattern='^back_to_main$'),
            ],
            # Config
            SELECT_CAR: [
                CallbackQueryHandler(select_car, pattern='^car_'),
                CallbackQueryHandler(back_to_main_handler, pattern='^back_to_main$'),
            ],
            SELECT_ENGINE: [
                CallbackQueryHandler(select_engine, pattern='^engine_'),
                CallbackQueryHandler(back_to_config_car, pattern='^back_to_config_car$'),
                CallbackQueryHandler(back_to_main_handler, pattern='^back_to_main$'),
            ],
            SELECT_SUSPENSION: [
                CallbackQueryHandler(select_suspension, pattern='^susp_'),
                CallbackQueryHandler(back_to_config_engine, pattern='^back_to_config_engine$'),
                CallbackQueryHandler(back_to_main_handler, pattern='^back_to_main$'),
            ],
            SELECT_BODYKIT: [
                CallbackQueryHandler(select_bodykit, pattern='^bodykit_'),
                CallbackQueryHandler(back_to_config_susp, pattern='^back_to_config_susp$'),
                CallbackQueryHandler(back_to_main_handler, pattern='^back_to_main$'),
            ],
            SELECT_WHEEL: [
                CallbackQueryHandler(select_wheel, pattern='^wheel_'),
                CallbackQueryHandler(back_to_config_bodykit, pattern='^back_to_config_bodykit$'),
                CallbackQueryHandler(back_to_main_handler, pattern='^back_to_main$'),
            ],
            CONFIG_SUMMARY: [
                CallbackQueryHandler(config_summary_action, pattern='^(place_order|restart_config)$'),
                CallbackQueryHandler(back_to_main_handler, pattern='^back_to_main$'),
            ],
            # Orders
            ORDER_REVIEW: [
                CallbackQueryHandler(confirm_order, pattern='^confirm_order$'),
                CallbackQueryHandler(back_to_main_handler, pattern='^back_to_main$'),
            ],
            ORDER_CONFIRMED: [
                CallbackQueryHandler(back_to_main_handler, pattern='^back_to_main$'),
            ],
            # Admin
            ADMIN_AUTH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_auth),
                CallbackQueryHandler(back_to_main_handler, pattern='^back_to_main$'),
            ],
            ADMIN_MENU: [
                CallbackQueryHandler(admin_menu_cb, pattern='^admin_(all|new|progress|stats|back)_'),
                CallbackQueryHandler(back_to_main_handler, pattern='^back_to_main$'),
            ],
            ADMIN_ORDER_LIST: [
                CallbackQueryHandler(handle_order_action, pattern='^admin_order_'),
                CallbackQueryHandler(admin_menu_cb, pattern='^admin_(all|new|progress|back)_'),
                CallbackQueryHandler(back_to_main_handler, pattern='^back_to_main$'),
            ],
            ADMIN_ORDER_DETAIL: [
                CallbackQueryHandler(handle_order_action, pattern='^admin_(order_|set_status_)'),
                CallbackQueryHandler(admin_menu_cb, pattern='^admin_back_'),
                CallbackQueryHandler(back_to_main_handler, pattern='^back_to_main$'),
            ],
        },
        fallbacks=[],
    )
    app.add_handler(conv)
    app.add_error_handler(lambda u, c: logger.error(f"Error: {c.error}"))

    logger.info("🤖 Bot started!")
    app.run_polling(drop_pending_updates=True)


# ==================== Back navigation helpers ====================

async def back_to_config_car(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['config'] = {}
    keyboard = [[InlineKeyboardButton(f"{c['name']} ({c['years']})", callback_data=f"car_{c['id']}")] for c in CARS]
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")])
    await update.callback_query.edit_message_text("🚗 Выберите автомобиль:", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_CAR


async def back_to_config_engine(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    car = context.user_data.get('config', {}).get('car')
    if not car:
        return await back_to_config_car(update, context)
    cid = car['id']
    engines = ENGINES.get(cid, [])
    keyboard = [[InlineKeyboardButton(e['name'], callback_data=f"engine_{e['id']}")] for e in engines]
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_config_car")])
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")])
    await update.callback_query.edit_message_text(f"⚙️ Выберите двигатель для {car['name']}:", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_ENGINE


async def back_to_config_susp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [[InlineKeyboardButton(s['name'], callback_data=f"susp_{sid}")] for sid, s in SUSPENSIONS.items()]
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_config_engine")])
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")])
    await update.callback_query.edit_message_text("🔧 Выберите подвеску:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_SUSPENSION


async def back_to_config_bodykit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [[InlineKeyboardButton(bk['name'], callback_data=f"bodykit_{bk['id']}")] for bk in BODYKITS]
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_config_susp")])
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")])
    await update.callback_query.edit_message_text("🎨 Выберите обвес:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_BODYKIT


if __name__ == '__main__':
    main()
