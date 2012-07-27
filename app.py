import os
from flask import Flask, request, render_template, redirect, url_for, session, flash
import urllib2
import urllib
from BeautifulSoup import BeautifulSoup
from collections import defaultdict
import urlparse
#import mechanize
import json

DEBUG = False

app = Flask(__name__)
app.config.from_object(__name__)

MIN_IMAGE_SIZE = 10000
MIN_IMAGE_WIDTH = 100
MIN_IMAGE_HEIGHT = 100

# SUGGESTED URLS
# 1. http://500px.com/popular?only=Fine%20Art
# 2. http://stevemccurry.com/galleries (images don't expand much)
# 3. http://timothyallen.blogs.bbcearth.com/ (too similar sizes)


@app.route("/")
def hello():
    return render_template('index.html')

@app.route("/contact")
def contact():
    return render_template('contact.html')

class ImageObject(object):
	def __init__(self, src, href, size, width, height):
		self.src = src
		self.href = href
		self.size = size
		self.width = width
		self.height = height

"""def getsizes(uri):
    # get file size *and* image size (None if not known)
    file = urllib2.urlopen(uri)
    size = file.headers.get("content-length")
    if size: size = int(size)
    p = ImageFile.Parser()
    while 1:
        data = file.read(1024)
        if not data:
            break
        p.feed(data)
        if p.image:
            return size, p.image.size
            break
    file.close()
    return size, None"""

import getimageinfo

def get_sizes(url):
	try:
		opened_file = urllib2.urlopen(url)
	except:
		print "the image url could not be opened"
		return 0, 0, 0
	
	try:
		image_type, width, height = getimageinfo.getImageInfo(opened_file)
	except:
		print "the image info could not be found"
		return 0, 0, 0

	try:
		#print opened_file.headers.get("content-length")
		size = int(opened_file.headers.get("content-length"))
	except:
		try:
			read_file = opened_file.read()
			size = int(len(read_file))
		except:
			size = 0
			print "the file size could not be found"
	opened_file.close()
	return size, width, height

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

def get_images_from_url(url):
	images = []

	if url.endswith('.jpg') or url.endswith('.png'):
		size, width, height = get_sizes(url)
		if size > 0:
			image = ImageObject(url, None, size, width, height)
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
			size, width, height = get_sizes(src)
			if width > MIN_IMAGE_WIDTH and height > MIN_IMAGE_HEIGHT:
				print width
				image = ImageObject(src, href, size, width, height)
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
	try:
		grid_width = int(request.args.get('grid_width'))
	except:
		grid_width = 140

	images = []

	url2 = request.args.get('url2')
	url3 = request.args.get('url3')
	for current_url in (url, url2, url3):
		image_batch = get_images_from_url(current_url)
		if image_batch is not None:
			images.extend(image_batch)

	if images is not None and len(images) > 4:
		return render_template('view_images.html', images=images, grid_width=grid_width)
	else:
		return render_template('try_again.html')

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)