from InstagramAPI import InstagramAPI
from mwclient import Site
import mwparserfromhell as mw
import datetime
import requests
import os 
from PIL import Image, ImageOps
import schedule
import time


def get_caption(templates):
	parsed_wikicode = templates[0].get('caption').value
	caption = parsed_wikicode.strip_code()
	return caption
	

def get_image_title(templates):
	parsed_wikicode = templates[0].get('image').value
	title = parsed_wikicode.strip_code()
	return title

def get_image(site, title):
	# vertical image: 1080x1350
	# horizontal image: 1080x566
	file = site.images[title]
	path = os.getcwd() + "/" + title
	with open(path, 'wb') as fd:
		file.download(fd)
	base = 1080
	img = Image.open(path)
	w, h = img.size
	wpercent = (base/float(w))
	hsize = int((float(h)*float(wpercent)))
	img = img.resize((base,hsize), Image.ANTIALIAS)
	w, h = img.size

	if h > 1350:
		img = ImageOps.expand(img,border=(int((h-1350)/2),0),fill='white')
		# img = img.crop((0, (h-1350)/2, w, h-((h-1350)/2)))
	elif h < 566:
		img = ImageOps.expand(img,border=(0,-int((h-566)/2)),fill='white')

	img.save(path)


def post(caption, path):
	user = InstagramAPI("wikipictureoftheday", "dreznerdrezner")
	user.login()  # login

	user.uploadPhoto(path, caption=caption)


def run():
	date = datetime.datetime.now()
	title = ("Template:POTD/" + str(date.year) + "-" + 
			str(date.month).zfill(2)  + "-" + str(date.day).zfill(2))
	site = Site('en.wikipedia.org')
	page = site.pages[title]
	templates = mw.parse(page.text()).filter_templates()


	caption = get_caption(templates)
	image_title = get_image_title(templates)
	get_image(site, image_title)
	post(caption, os.getcwd() + "/" + image_title)
	os.remove(os.getcwd() + "/" + image_title)


def schedule_task():
	schedule.every().day.at("08:00").do(run)

	while True:
		schedule.run_pending()
		time.sleep(60) # wait minutes


def main():
	run()

run()
schedule_task()
