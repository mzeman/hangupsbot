import os
import io
import time
import re
import random
import asyncio
import aiohttp
import praw
import hangups

# If the image upload ever breaks change this to False
upload_images = True

def _initialise(Handlers, bot=None):
    Handlers.register_user_command(["reddit"])
    return []


def reddit(bot, event, *args):
    """ This plugin pulls a random post from rising and hot posts on reddit if
    rising didnt have enough interesting submissions. Usage: /bot reddit sub"""
    if len(args) == 0:
        target_sub = "aww"
    if len(args) > 0:
        target_sub = args[0]

    # Default to aww if there's no argument
    if not args:
        target_sub = "aww"
    try:
        if not target_sub:
            target_sub = "aww"
        r = praw.Reddit(user_agent='Dekriz')
        submissions = r.get_subreddit(target_sub).get_rising(limit=50)
        list_hot = []
        link_title = []
        link_url = []
        for submission in submissions:
            if "i.imgur.com/"in submission.url:
                list_hot.append(submission.url)
                continue
            if "?" in submission.url:
                continue
            link_title.append(submission.title)
            link_url.append(submission.url)
        print(len(list_hot))
        # If there's not enough submissions in rising pull from top
        if len(list_hot) < 5:
            submissions = r.get_subreddit(target_sub).get_hot(limit=50)
            for submission in submissions:
                if "i.imgur.com/" in submission.url:
                    list_hot.append(submission.url)
                if "?" in submission.url:
                    continue
                if "imgur.com/removed" in submission.url:
                    continue
                link_title.append(submission.title)
                link_url.append(submission.url)
        # Assume if there's nothing at this point that it's a self post subreddit
        if len(list_hot) < 1:
            rand = random.randrange(0,len(link_title))
            link_url = link_url[rand]
            link_title = link_title[rand]
            bot.send_html_to_conversation(event.conv_id,"<a href=\"" + link_url + "\">" + link_title + "</a>")

        else:
            link_image=list_hot[random.randrange(0,len(list_hot))]
            if(upload_images):
                try:
                    filename = os.path.basename(link_image)
                    s = yield from aiohttp.request('get', list_hot[random.randrange(0,len(list_hot))])
                    raw = yield from s.read()
                    image_data = io.BytesIO(raw)

                    image_id = yield from bot._client.upload_image(image_data, filename=filename)

                    bot.send_message_segments(event.conv.id_, None, image_id=image_id)
                # In case uploading breaks just send the link
                except Exception as e:
                     bot.send_message_parsed(event.conv,link_image)
                     bot.send_html_to_conversation(event.conv_id, "<i>PS: uploading is broken. set upload_images to False or fix uploading.</i>")
            else:
                bot.send_message_parsed(event.conv,link_image) 
    except Exception as e:
        bot.send_html_to_conversation(event.conv_id, "<i>couldn't pull from reddit, please check reddit name and try again. reddit could also be down. </i>")
        print("{}".format(e))
