from api_wrapper import *
from audio import *
from config import *
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

START_MESSAGE = "I can get you the top headlines and breaking news for a country (in the country's official language) in an audited format.\n" \
                "\nHere is what I can do:\n\n" \
                "1- Get news for a country from the country's sources.\n" \
                "2- Get news for a country from the country's sources about a specific category. Here are possible " \
                "categories:\n" \
                "   - business\n" \
                "   - entertainment\n" \
                "   - general\n" \
                "   - health\n" \
                "   - science\n" \
                "   - sports\n" \
                "   - technology\n\n" \
                "For option 1, type /getnews\n" \
                "For option 2, type /getnews_category\n"

INVALID_RESPONSE_ERROR = "I'm not sure I understand your response. To see what I can do press /start"

api = Api(NEWS_API_KEY)


# Commands
async def start_command(update: Update,context):
    """handle the /start command"""
    await update.message.reply_text(START_MESSAGE)


async def getnews(update: Update,context):
    """handle the /getnews command"""
    info_message = "To get top headlines and breaking news in an audited format:\n" \
                   "type this without '< >':\n <insert your country code according to ISO 3166-1>'"

    await update.message.reply_text(info_message)


async def getnews_category(update: Update,context):
    """handle the /getnews_category command"""

    info_message = "Here are possible categories:\n" \
                   "   - business\n" \
                   "   - entertainment\n" \
                   "   - general\n" \
                   "   - health\n" \
                   "   - science\n" \
                   "   - sports\n" \
                   "   - technology\n\n" \
                   "To get top headlines and breaking news in an audited format:\n" \
                   "type this without '< >':\n <insert your country code according to ISO 3166-1>'<insert space> " \
                   "<insert one of the categories above>"

    await update.message.reply_text(info_message)


# Logic
def process_user_message(user_message: str, output_file_name:str, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Create audio if applicable and return the absolute path.
    If not applicable returns error message"""

    response_data = user_message.split(" ")

    # keep track if audio is generated
    context.user_data["generated_audio"] = False

    # user possibly asked for news in a country
    if len(response_data) == 1:

        # get list of articles
        country_code = response_data[0]

        # if given country code is valid
        if helpers.is_ISO_3166_country_code(country_code):

            articles = api.get_top_headlines(country_code)

            # intro to start the audio with
            intro = f"Latest news in {helpers.get_country_name(country_code)}"

            # create audio
            audio = Audio.from_country_code(articles, country_code, intro, output_file_name)
            audio.create_audio()

            context.user_data["generated_audio"] = True
            bot_response = audio.get_audio_path()

        # given country code is not valid
        else:
            bot_response = f"Country code {country_code} is not supported. Please check if it is in ISO 3166 format.\n" \
                           f"If it is, please contact admin"

    # user possibly asked for news in a country in a specific category
    elif len(response_data) == 2:

        # get list of articles
        country_code = response_data[0]
        category = response_data[1]

        # if given country code is valid
        if helpers.is_ISO_3166_country_code(country_code):

            if category in api.CATEGORIES:

                articles = api.get_top_headlines(country_code, category)

                # intro to start the audio with
                intro = f"Latest news in {helpers.get_country_name(country_code)} about {category}"

                # create audio
                audio = Audio.from_country_code(articles, country_code, intro, output_file_name)
                audio.create_audio()

                context.user_data["generated_audio"] = True
                bot_response = audio.get_audio_path()

            else:
                bot_response = f"Category {category} is not supported. To see the supported categories type /getnews_category"

        else:
            bot_response = f"Country code {country_code} is not supported. Please check if it is in ISO 3166 format.\n" \
                           f"If it is, please contact admin"

    else:
        bot_response = INVALID_RESPONSE_ERROR

    return bot_response


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """"Send audio to chat if audio was created else send error message """

    # identify if group or private
    message_type = update.message.chat.type

    # user response
    user_response = update.message.text

    user_id = update.message.chat.id
    output_file_name = f"{user_id}.mp3"

    if message_type == "group":

        if BOT_USERNAME in user_response:
            user_response = user_response.replace(BOT_USERNAME, "")
            bot_response = process_user_message(user_response, output_file_name, context)

        else:
            return
    else:
        bot_response = process_user_message(user_response, output_file_name, context)


    # if audio is generated
    # send audio to chat
    if context.user_data["generated_audio"]:
        print("sending the audio")
        audio_file = open(output_file_name, 'rb')
        await update.message.reply_audio(audio= audio_file)
        context.user_data["generated_audio"] = False

    # if audio is not generated
    # send error message
    else:
        await update.message.reply_text(bot_response)


# Debugger function for the developer
async def log_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")


if __name__ == "__main__":
    print("Starting bot")
    app = Application.builder().token(TELEGRAM_BOT_API_KEY).build()

    # Handling Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler("getnews", getnews))
    app.add_handler(CommandHandler("getnews_category", getnews_category))

    # Handling Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    app.add_error_handler(log_error)

    # Polls the bot
    print("Polling")
    # Check for updates every poll_interval
    app.run_polling(poll_interval=POLL_INTERVAL_SECONDS)
