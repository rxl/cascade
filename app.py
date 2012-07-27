import os
from flask import Flask, request, render_template, redirect, url_for, session, flash
import urllib2
import urllib
from BeautifulSoup import BeautifulSoup
from collections import defaultdict
import urlparse
#import mechanize
import json

DEBUG = True

app = Flask(__name__)
app.config.from_object(__name__)

MIN_WIDTH = 200
GRID_WIDTH = 200
MIN_IMAGE_SIZE = 10000

# SUGGESTED URLS
# 1. http://500px.com/popular?only=Fine%20Art
# 2. http://stevemccurry.com/galleries (images don't expand much)
# 3. http://timothyallen.blogs.bbcearth.com/ (too similar sizes)

@app.route("/")
def hello():
    return render_template('index.html')

def get_size(url):
	try:
		opened_file = urllib2.urlopen(url)
	except:
		print "the image url could not be opened"
		return 0
	try:
		size = int(opened_file.headers.get("content-length"))
	except:
		try:
			size = int(len(opened_file.read()))
		except:
			size = 0
			print "the file size could not be found"
	opened_file.close()
	return size

def get_file_data_and_size(url):
	try:
		opened_file = urllib2.urlopen(url)
	except:
		print "the image url could not be opened"
		return 0
	#try:
	#	size = int(file.headers.get("content-length"))
	#except:
	try:
		file_data = urllib.quote(opened_file.read())
	except:
		file_data = None
		print "the file could not be read"
	try:
		size = int(len(file_data))
	except:
		size = 0
		print "the file size could not be found"
	opened_file.close()
	#print size
	return (file_data, size)

class ImageObject(object):
	def __init__(self, src, href, size):
		self.src = src
		self.href = href
		self.size = size

def get_images_from_url(url):
	images = []

	if url.endswith('.jpg') or url.endswith('.png'):
		size = get_size(url)
		if size > 1:
			image = ImageObject(url, None, size)
			images.append(image)
		else:
			return None
	else:
		html = None
		try:
			page = urllib2.urlopen(url)
			undigested_html = page.read()
			html = BeautifulSoup(undigested_html)
		except:
			return None

		image_tags = html.findAll('img')
		for image in image_tags:
			src = urlparse.urljoin(url, image.get('src'))
			href = None
			if image.parent.name == 'a':
				href = urlparse.urljoin(url, image.parent.get('href'))
			size = get_size(src)
			image = ImageObject(src, href, size)
			if image.size > MIN_IMAGE_SIZE:
				images.append(image)
		images.sort(key=lambda x: x.size, reverse=True)

	return images

@app.route("/getlargestimage/", methods=['POST', 'GET'])
def get_largest_image_from_url():
	if request.method == 'POST':
		url = request.form['url']
		barcode = request.form['barcode']
	else:
		url = request.args.get('url')
		barcode = request.args.get('barcode')
	images = get_images_from_url(url)
	if len(images) > 0:
		image = images[0]
		response = { "success" : True, "src": image.src, "barcode": barcode }
	else:
		response = { "success" : False, "error": "could not find any images" }
	return json.dumps(response)
	#else:
	#	return "404 - Page Not Found"

@app.route("/displayimages/")
def display_images():
	url = request.args.get('url')
	if url is None:
		return render_template('try_again.html')

	images = get_images_from_url(url)
	#for image in images:
	#	print image.size
	if images is not None and len(images) > 4:
		return render_template('view_images.html', images=images, min_width=MIN_WIDTH, grid_width=GRID_WIDTH)
	else:
		return render_template('try_again.html')

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)