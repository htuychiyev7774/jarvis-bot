import os
import logging
import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

import config
import google_auth
import google_calendar
import gmail_service
import notion_service
import google_drive

# Configure Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Track sent calendar event notifications in-memory to prevent duplicate reminders
NOTIFIED_EVENTS = set()

def owner_only(func):
    """Decorator to restrict commands to the authorized owner only."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not update.effective_user:
            return
        if update.effective_user.id != config.TELEGRAM_OWNER_ID:
            logger.warning(f"Unauthorized access attempt by user {update.effective_user.id} ({update.effective_user.username})")
            await update.message.reply_text("Kechirasiz, siz ushbu botni boshqarish huquqiga ega emassiz! (Unauthorized)")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

@owner_only
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a greeting message and lists available commands."""
    welcome_text = (
        "🤖 **Jarvis Telegram Bot ishga tushdi!**\n\n"
        "Men sizning shaxsiy yordamchingizman. Quyidagi buyruqlardan foydalanishingiz mumkin:\n\n"
        "📅 **Kalendar buyruqlari:**\n"
        "• /calendar_list - Yaqin atrofdagi uchrashuvlarni ko'rish\n"
        "• /calendar_add [xabar] - Yangi uchrashuv qo'shish (Masalan: `Meeting at tomorrow 15:00`)\n\n"
        "📧 **E-pochta buyruqlari:**\n"
        "• /gmail_check - O'qilmagan xatlarni tekshirish va guruhlash\n\n"
        "📝 **Notion (Rejalar) buyruqlari:**\n"
        "• /notion_list - Bajarilmagan vazifalar ro'yxati\n"
        "• /notion_add [nomi] - Yangi vazifa qo'shish\n"
        "• /notion_complete [index] - Vazifani bajarilgan deb belgilash\n\n"
        "💾 **Google Drive buyruqlari:**\n"
        "• /drive_list [qidiruv] - Drive fayllarini izlash va ko'rish\n"
        "• /drive_download [id] - Faylni yuklab olish va yuborish\n"
        "• *Fayl yuborish* - Istalgan faylni Telegram orqali yuborsangiz, uni avtomatik Drive'ga yuklayman."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

@owner_only
async def calendar_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists upcoming events from Google Calendar."""
    await update.message.reply_text("📅 Google Kalendarni tekshirmoqdaman...")
    try:
        events = google_calendar.list_upcoming_events(max_results=5)
        if not events:
            await update.message.reply_text("Hech qanday uchrashuvlar topilmadi.")
            return

        response = "📅 **Yaqinlashayotgan uchrashuvlar:**\n\n"
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            # Format datetime
            dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
            formatted_time = dt.strftime('%Y-%m-%d %H:%M')
            summary = gmail_service.escape_tg_html(event.get('summary', 'Mavzusiz'))
            response += f"• <b>{formatted_time}</b> - {summary}\n"
            
        await update.message.reply_text(response, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Calendar list error: {e}")
        await update.message.reply_text("❌ Kalendarni yuklashda xatolik yuz berdi. Google auth sozlamalari to'g'ri o'rnatilganligini tekshiring.")

@owner_only
async def calendar_add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Adds a new event to Google Calendar."""
    if not context.args:
        await update.message.reply_text("Iltimos, uchrashuv tafsilotlarini yozing. Masalan: `/calendar_add Muhokama at tomorrow 14:00`")
        return

    text = " ".join(context.args)
    await update.message.reply_text("✍️ Buyruq matnini tahlil qilmoqdaman...")
    
    try:
        start_dt, title, desc = google_calendar.parse_datetime_nl(text)
        
        # Confirming with user
        await update.message.reply_text(
            f"📅 Yangi uchrashuv yaratilmoqda:\n"
            f"• **Nomi:** {title}\n"
            f"• **Vaqti:** {start_dt.strftime('%Y-%m-%d %H:%M')}\n"
            f"• **Tafsilotlar:** {desc}"
        )
        
        event = google_calendar.create_calendar_event(title, start_dt, description=desc)
        await update.message.reply_text(f"✅ Uchrashuv muvaffaqiyatli qo'shildi! Havola: {event.get('htmlLink')}")
    except Exception as e:
        logger.error(f"Calendar add error: {e}")
        await update.message.reply_text(f"❌ Xatolik yuz berdi: {e}")

@owner_only
async def gmail_check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually fetches and categorizes unread emails."""
    await update.message.reply_text("📧 Pochtangizni tekshirmoqdaman...")
    try:
        unread = gmail_service.fetch_unread_emails(max_results=5)
        if not unread:
            await update.message.reply_text("Inbox toza. Yangi o'qilmagan xabarlar yo'q.")
            return

        await update.message.reply_text(f"📥 {len(unread)} ta yangi xat topildi. Tahlil qilinmoqda...")
        
        for msg in unread:
            details = gmail_service.get_email_details(msg['id'])
            category, summary = gmail_service.categorize_and_summarize(details)
            
            # Format message securely
            sender_esc = gmail_service.escape_tg_html(details['sender'])
            subject_esc = gmail_service.escape_tg_html(details['subject'])
            summary_esc = gmail_service.escape_tg_html(summary)
            
            message_text = (
                f"📧 <b>Yangi Xat!</b>\n\n"
                f"👤 <b>Kimdan:</b> {sender_esc}\n"
                f"📝 <b>Mavzu:</b> {subject_esc}\n"
                f"🏷️ <b>Turkum:</b> {category}\n"
                f"📄 <b>Xulosa (AI):</b> {summary_esc}"
            )
            await update.message.reply_text(message_text, parse_mode="HTML")
            
            # Mark as read to avoid duplicate alerts
            gmail_service.mark_email_as_read(msg['id'])
            
    except Exception as e:
        logger.error(f"Gmail check error: {e}")
        await update.message.reply_text("❌ Gmail bilan aloqada xatolik yuz berdi.")

@owner_only
async def notion_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists pending tasks in the Notion database."""
    await update.message.reply_text("📝 Notion ro'yxatini yuklamoqdaman...")
    try:
        tasks = notion_service.get_pending_tasks()
        if not tasks:
            await update.message.reply_text("Barcha rejalar bajarilgan yoki ro'yxat bo'sh.")
            return
        
        # Save tasks to user_data for references in selection
        context.user_data['pending_tasks'] = tasks
        
        response = "📝 **Bajarilmagan rejalar ro'yxati:**\n\n"
        for idx, task in enumerate(tasks, start=1):
            title_esc = gmail_service.escape_tg_html(task['title'])
            response += f"{idx}. {title_esc}\n"
            
        response += "\nRejani bajarilgan deb belgilash uchun: `/notion_complete [tartib raqami]` yozing."
        await update.message.reply_text(response, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Notion list error: {e}")
        await update.message.reply_text("❌ Notion ma'lumotlar bazasini yuklashda xatolik. Token yoki DB ID noto'g'ri o'rnatilgan bo'lishi mumkin.")

@owner_only
async def notion_add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Adds a new task to Notion."""
    if not context.args:
        await update.message.reply_text("Iltimos, vazifa nomini yozing. Masalan: `/notion_add Kitob o'qish`")
        return
        
    title = " ".join(context.args)
    await update.message.reply_text(f"📝 Notion'ga qo'shilmoqda: '{title}'...")
    try:
        notion_service.add_task(title)
        await update.message.reply_text("✅ Vazifa Notion bazasiga qo'shildi!")
    except Exception as e:
        logger.error(f"Notion add error: {e}")
        await update.message.reply_text(f"❌ Xatolik yuz berdi: {e}")

@owner_only
async def notion_complete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Marks a Notion task completed by index number."""
    if not context.args:
        await update.message.reply_text("Iltimos, bajarilgan reja tartib raqamini yozing. Masalan: `/notion_complete 1`")
        return
        
    try:
        idx = int(context.args[0]) - 1
    except ValueError:
        await update.message.reply_text("Iltimos, faqat raqam kiriting.")
        return
        
    tasks = context.user_data.get('pending_tasks')
    if not tasks:
        # Load tasks again if user_data is empty
        try:
            tasks = notion_service.get_pending_tasks()
            context.user_data['pending_tasks'] = tasks
        except Exception as e:
            await update.message.reply_text("Vazifalar ro'yxatini yuklab bo'lmadi.")
            return
            
    if not tasks or idx < 0 or idx >= len(tasks):
        await update.message.reply_text("Noto'g'ri tartib raqami kiritildi. /notion_list buyrug'i orqali ro'yxatni ko'ring.")
        return
        
    target_task = tasks[idx]
    await update.message.reply_text(f"⚙️ '{target_task['title']}' vazifasi yakunlanmoqda...")
    try:
        success = notion_service.complete_task(target_task['id'])
        if success:
            await update.message.reply_text(f"✅ '{target_task['title']}' muvaffaqiyatli bajarildi deb belgilandi!")
            # Update user_data cache
            tasks.pop(idx)
            context.user_data['pending_tasks'] = tasks
        else:
            await update.message.reply_text("❌ Vazifani bajarilgan deb belgilashda muammo yuz berdi.")
    except Exception as e:
        logger.error(f"Notion complete error: {e}")
        await update.message.reply_text(f"❌ Xatolik: {e}")

@owner_only
async def drive_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists files in Google Drive."""
    query = " ".join(context.args) if context.args else None
    msg_status = "qidirilmoqda..." if query else "yuklanmoqda..."
    await update.message.reply_text(f"📂 Google Drive'dagi fayllar {msg_status}")
    
    try:
        files = google_drive.list_drive_files(search_query=query, max_results=10)
        if not files:
            await update.message.reply_text("Hech qanday fayl topilmadi.")
            return
            
        response = "📂 **Google Drive fayllari:**\n\n"
        for f in files:
            size_kb = int(f.get('size', 0)) // 1024
            size_str = f"({size_kb} KB)" if size_kb > 0 else ""
            name_esc = gmail_service.escape_tg_html(f.get('name', 'Nomsiz'))
            response += f"• <code>{f.get('id')}</code> - {name_esc} {size_str}\n"
            
        response += "\nYuklab olish uchun: `/drive_download [fayl_id]`"
        await update.message.reply_text(response, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Drive list error: {e}")
        await update.message.reply_text("❌ Google Drive bilan bog'lanishda xatolik.")

@owner_only
async def drive_download_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Downloads a file from Google Drive and sends it to the user."""
    if not context.args:
        await update.message.reply_text("Iltimos, fayl ID raqamini ko'rsating. Masalan: `/drive_download [id]`")
        return
        
    file_id = context.args[0].strip()
    await update.message.reply_text("📥 Faylni Drive'dan yuklab olmoqdaman...")
    
    try:
        # Download and secure the path inside sandbox
        local_path = google_drive.download_drive_file(file_id)
        
        # Send document to user
        await update.message.reply_text("📤 Telegram'ga yuklanmoqda...")
        with open(local_path, 'rb') as doc:
            await update.message.reply_document(document=doc)
            
        # Clean up local file after sending
        os.remove(local_path)
    except PermissionError as pe:
        await update.message.reply_text(f"⚠️ Xavfsizlik xatoligi: {pe}")
    except Exception as e:
        logger.error(f"Drive download error: {e}")
        await update.message.reply_text(f"❌ Faylni yuklab olishda xatolik yuz berdi: {e}")

@owner_only
async def handle_document_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Automatically downloads documents uploaded via Telegram and uploads them to Drive."""
    document = update.message.document
    file_name = document.file_name
    
    # 1. Sanitize local destination path using os.path.basename
    safe_file_name = os.path.basename(file_name)
    if not safe_file_name or safe_file_name in ['.', '..']:
        safe_file_name = f"telegram_upload_{int(datetime.datetime.now().timestamp())}"
        
    local_path = os.path.join(config.DOWNLOADS_DIR, safe_file_name)
    abs_local_path = os.path.abspath(local_path)
    abs_downloads_dir = os.path.abspath(config.DOWNLOADS_DIR)
    
    # Strict boundary check (trailing separator)
    if not abs_local_path.startswith(abs_downloads_dir + os.sep):
        await update.message.reply_text("⚠️ Xavfsizlik sababli noto'g'ri fayl nomi yuklash rad etildi.")
        return

    await update.message.reply_text(f"📥 Fayl qabul qilindi. Google Drive'ga yuklash boshlandi...")
    
    try:
        # 2. Download from Telegram to local sandbox
        tg_file = await context.bot.get_file(document.file_id)
        await tg_file.download_to_drive(custom_path=abs_local_path)
        
        # 3. Upload to Google Drive
        drive_file = google_drive.upload_to_drive(abs_local_path, safe_file_name)
        
        await update.message.reply_text(f"✅ Fayl muvaffaqiyatli yuklandi!\n• ID: <code>{drive_file.get('id')}</code>\n• Nomi: {drive_file.get('name')}", parse_mode="HTML")
        
        # Clean up local file
        os.remove(abs_local_path)
    except PermissionError as pe:
        await update.message.reply_text(f"⚠️ Xavfsizlik xatoligi: {pe}")
    except Exception as e:
        logger.error(f"Telegram-to-Drive upload error: {e}")
        await update.message.reply_text(f"❌ Faylni Drive'ga joylashda xatolik: {e}")

# --- Background Scheduler Jobs ---

async def gmail_notify_job(context: ContextTypes.DEFAULT_TYPE):
    """Background job that checks for new emails and alerts the owner."""
    try:
        unread = gmail_service.fetch_unread_emails(max_results=5)
        if not unread:
            return
            
        for msg in unread:
            details = gmail_service.get_email_details(msg['id'])
            category, summary = gmail_service.categorize_and_summarize(details)
            
            # Format message securely
            sender_esc = gmail_service.escape_tg_html(details['sender'])
            subject_esc = gmail_service.escape_tg_html(details['subject'])
            summary_esc = gmail_service.escape_tg_html(summary)
            
            message_text = (
                f"📧 <b>Yangi Xat (Avtomatik)!</b>\n\n"
                f"👤 <b>Kimdan:</b> {sender_esc}\n"
                f"📝 <b>Mavzu:</b> {subject_esc}\n"
                f"🏷️ <b>Turkum:</b> {category}\n"
                f"📄 <b>Xulosa (AI):</b> {summary_esc}"
            )
            # Send notification to the owner
            await context.bot.send_message(chat_id=config.TELEGRAM_OWNER_ID, text=message_text, parse_mode="HTML")
            
            # Mark as read
            gmail_service.mark_email_as_read(msg['id'])
    except Exception as e:
        logger.error(f"Error in Gmail background scheduler job: {e}")

async def calendar_reminder_job(context: ContextTypes.DEFAULT_TYPE):
    """Background job that checks Google Calendar for upcoming meetings."""
    try:
        events = google_calendar.list_upcoming_events(max_results=5)
        if not events:
            return
            
        now_utc = datetime.datetime.utcnow()
        
        for event in events:
            event_id = event.get('id')
            if event_id in NOTIFIED_EVENTS:
                continue
                
            start = event['start'].get('dateTime')
            if not start:
                continue
                
            # Parse event start time
            event_start = datetime.datetime.fromisoformat(start.replace('Z', '+00:00')).replace(tzinfo=None)
            time_diff = event_start - now_utc
            
            # Alert if the event starts within the next 15 minutes and in the future
            if datetime.timedelta(seconds=0) < time_diff <= datetime.timedelta(minutes=15):
                summary_esc = gmail_service.escape_tg_html(event.get('summary', 'Mavzusiz'))
                desc_esc = gmail_service.escape_tg_html(event.get('description', 'Izohsiz'))
                local_time_str = event_start.strftime('%H:%M')
                
                alert_text = (
                    f"⏰ <b>Uchrashuv yaqinlashmoqda! (Eslatma)</b>\n\n"
                    f"📅 <b>Nomi:</b> {summary_esc}\n"
                    f"🕒 <b>Boshlanish vaqti:</b> {local_time_str}\n"
                    f"📝 <b>Tafsilotlar:</b> {desc_esc}"
                )
                
                await context.bot.send_message(chat_id=config.TELEGRAM_OWNER_ID, text=alert_text, parse_mode="HTML")
                NOTIFIED_EVENTS.add(event_id)
                
    except Exception as e:
        logger.error(f"Error in Calendar background scheduler job: {e}")

def main():
    """Starts the bot application and registers command/message handlers."""
    # Create the application
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", start_command))
    application.add_handler(CommandHandler("calendar_list", calendar_list_command))
    application.add_handler(CommandHandler("calendar_add", calendar_add_command))
    application.add_handler(CommandHandler("gmail_check", gmail_check_command))
    application.add_handler(CommandHandler("notion_list", notion_list_command))
    application.add_handler(CommandHandler("notion_add", notion_add_command))
    application.add_handler(CommandHandler("notion_complete", notion_complete_command))
    application.add_handler(CommandHandler("drive_list", drive_list_command))
    application.add_handler(CommandHandler("drive_download", drive_download_command))
    
    # Register document upload handler
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document_upload))

    # Initialize Job Queue for background monitoring
    job_queue = application.job_queue
    if job_queue:
        # Check Gmail every 5 minutes (300 seconds)
        job_queue.run_repeating(gmail_notify_job, interval=300, first=10)
        # Check Calendar every 5 minutes (300 seconds)
        job_queue.run_repeating(calendar_reminder_job, interval=300, first=15)
        logger.info("Background job scheduler initialized.")
    else:
        logger.warning("Job queue is unavailable. Background checks for Gmail and Calendar are disabled.")

    # Start the Bot
    logger.info("Bot started polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
