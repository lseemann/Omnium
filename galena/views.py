# Create your views here.
from django.template.loader import get_template
from django.template import Context,RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from galena.models import *
from django import forms
from operator import itemgetter, attrgetter
import csv
import time
import os
import ftplib
from ftplib import FTP

path_to_results = '' # A directory where results files will be saved
ftp_server = ''
ftp_username = ''
ftp_password = ''
ftp_path = ''


def validResult(value):
	if value != None and float(value) and value != 999:
		return True
	else:
		return False

def ordinal(value):
    """
    Converts an integer to its ordinal as a string. 1 is '1st', 2 is '2nd',
    3 is '3rd', etc. Works for any integer.
    """
    try:
        value = int(value)
    except ValueError:
        return value
    t = (('th'), ('st'), ('nd'), ('rd'), ('th'), ('th'), ('th'), ('th'), ('th'), ('th'))
    if value % 100 in (11, 12, 13): # special case
        return u"%d%s" % (value, t[0])
    return u'%d%s' % (value, t[value % 10])

def createFiles(*changedraces):
	races = Race.objects.all()
	fields = Field.objects.all()
	html = ""
	for field in fields:
		if field.slug == 'mp' or field.slug == 'wp':
			elite = True
		else:
			elite = False

		riders = Rider.objects.filter(field=field).exclude(dq=1).order_by('-omnium','tt_order','lname')
		place = 1
		for rider in riders:
			for race in races:
				thisPoints = race.slug+'_points'
				thisPlace = race.slug+'_place'
				setattr(rider, thisPoints, getattr(rider, thisPoints)())
				# If this is a valid result, display an ordinal of the result
				if validResult(getattr(rider, thisPlace)):
					setattr(rider, thisPlace, ordinal(getattr(rider, thisPlace)) + ' place')
				else:
					setattr(rider, thisPlace, '-')
			# 999 means they DNF or DNS'd the TT
			if rider.tt_order == 999 and rider.omnium == 0:
				rider.place = '-'
			else:
				rider.place = str(place)
			place += 1

		now = time.strftime('%l:%M %p on %B %-d, %Y')
		f = open(path_to_results + 'omnium-' + field.slug+ '.php','w')
		t = get_template('omnium-web.html')
		c = Context({
			'riders': riders,
			'field': field,
			'elite': elite,
			'time': now,
		})
		html = t.render(c)

		f.writelines(html)
		f.close()

		f = open(path_to_results + 'omnium-' + field.slug+ '-print.php','w')
		t = get_template('omnium-print.html')
		c = Context({
			'riders': riders,
			'field': field,
			'elite': elite,
			'time': now,
		})
		html = t.render(c)
		f.writelines(html)
		f.close()

		f = open(path_to_results + 'usac/omnium-' + field.slug+ '-for-usac.txt','w')
		t = get_template('omnium-csv.html')
		c = Context({
			'riders': riders,
			'field': field,
			'time': now,
		})
		html = t.render(c)
		f.writelines(html)
		f.close()


		# Now let's create PHP files for each individual race, for this field
		for race in changedraces:
			race = Race.objects.get(slug=race)
			results = Result.objects.filter(field=field,race=race).order_by('order','place','lname')

			f = open(path_to_results+race.slug+'-'+field.slug+'.php','w')
			t = get_template('race-web.html')
			c = Context({
				'results': results,
				'field': field,
				'time': now,
				'race':race,
			})
			html = t.render(c)
			f.writelines(html)
			f.close()

			f = open(path_to_results+race.slug+'-'+field.slug+'-print.php','w')
			t = get_template('race-print.html')
			c = Context({
				'results': results,
				'field': field,
				'time': now,
				'race':race,
			})
			html = t.render(c)

			f.writelines(html)
			f.close()

# Update the placings for a riders omnium tracking. This does not affect race results pages, just the omnium.
def field(request,thisField):
	fields = Field.objects.all()

	try:
		thisField = Field.objects.get(slug=thisField)
		if thisField.slug == 'mp' or thisField.slug == 'wp':
			elite = True
		else:
			elite = False
	except Race.DoesNotExist:
		raise Http404()

	riders = Rider.objects.filter(field=thisField).order_by('lname')
	memo = ''
	values = 'x'
	if request.method == 'POST':

		for rider in riders:
			if elite:
				try:
					rider.cr_place = int(request.POST.get(unicode(rider.usac)+'#cr_place'))
				except:
					pass
			try:
				rider.tt_place = int(request.POST.get(unicode(rider.usac)+'#tt_place'))
			except:
				pass
			try:
				rider.rr_place = int(request.POST.get(unicode(rider.usac)+'#rr_place'))
			except:
				pass
			try:
				rider.crit_place = int(request.POST.get(unicode(rider.usac)+'#crit_place'))
			except:
				pass
			try:
				rider.sprint_place = int(request.POST.get(unicode(rider.usac)+'#sprint_place'))
			except:
				pass
			rider.save()
		memo = '<i class="icon-ok icon-white"></i> Changes made.'

	createFiles()


	# Regardless of whether form has been submitted, do following
	for rider in riders:
		if elite:
			rider.cr_points = rider.cr_points()
		else:
			rider.cr_points = 0
		rider.tt_points = rider.tt_points()
		rider.rr_points = rider.rr_points()
		rider.crit_points = rider.crit_points()
		rider.sprint_points = rider.sprint_points()


	t = get_template('field.html')
	c = Context({
		'fields': fields,
		'thisField': thisField,
		'riders': riders,
		'values': values,
		'memo' : memo,
		'elite': elite,
	})
	html = t.render(c)
	return HttpResponse(html)

def addresults(request):
	errors = successes = ''
	results = ''
	fields = Field.objects.all()
	if request.method == 'POST':
		race = Race.objects.get(slug = request.POST.get('race'))
		csvfile = request.FILES.get('csvfile')
		try:
			results = csv.DictReader(csvfile)
		except:
			errors = errors + '<li>File note found</ul>'

		# Delete any results for this race so that we can begin anew.
		Result.objects.filter(race=race).delete()

		# DOUBLE CHECK THESE FIELD HEADERS WITH KNAUFF
		for result in results:
			usac = result['USAC LICENSE']
			place = result['Place']
			fname = result['FIRST NAME']
			lname = result['LAST NAME']
			team = result['TEAM']
			resultField = result['CATEGORY ENTERED']
			if race.slug == 'tt' and result['Time']:
				tt_time = result['Time']
			else:
				tt_time = 0
			field = Field.objects.get(full = resultField)

			result = Result()
			result.lname = lname
			result.fname = fname
			result.place = place
			result.team = team
			result.race = race
			result.field = field
			result.tt_time = tt_time
			if usac.isdigit():
				result.usac = usac
			result.save()
			successes += '<li>' + unicode(result) + '\n'

			# Now we see if the rider is doing the omnium. Are they in the system for this field?
			try:
				rider = Rider.objects.get(usac=usac,field=field,dq=False)
				result.in_omnium = 1
				result.save()
				if place.isdigit():
					if race.slug == 'cr':
						rider.cr_place = int(place)
					elif race.slug == 'tt':
						rider.tt_place = int(place)
						rider.tt_time = tt_time
					elif race.slug == 'rr':
						rider.rr_place = int(place)
					elif race.slug == 'crit':
						rider.crit_place = int(place)
					elif race.slug == 'sprint':
						rider.sprint_place = int(place)

				rider.save()
				successes += '<li> Omnium results for ' + unicode(rider) + ' updated\n'

			except:
				errors += '<li>' + fname + ' ' + lname + ' (' + str(usac) + ") was not found in the " + field.full + " omnium\n"

		createFiles(race.slug)

	t = get_template('addresults.html')
	c = Context({
		'fields': fields,
		'errors': errors,
		'successes': successes,

	})
	html = t.render(c)
	return HttpResponse(html)

def addriders(request):
	fields = Field.objects.all()
	errors = successes = ''

	if request.method == 'POST':
		thisField = request.POST.get('field')
		field = Field.objects.get(slug=thisField)
		newriders = request.POST.get('newriders')
		newriders = newriders.split('\n')
		for newrider in newriders:
			newrider = newrider.split(',')
			n = Rider()
			n.fname = newrider[0]
			n.lname = newrider[1]
			n.team = newrider[2]
			n.usac = newrider[3]
			if not n.usac.isdigit():
				errors += '<li>' + unicode(n) + ' was not entered: invalid USAC number</li>'
			else:
				try:
					check = Rider.objects.get(usac=n.usac)
					errors += '<li>' + unicode(n) + ' is already in the system</li>'
				except:
					n.field = field
					n.save()
					successes += '<li>' + unicode(n) + ' successfully added</li>'

	t = get_template('addriders.html')
	c = Context({
		'fields': fields,
		'successes': successes,
		'errors': errors,
	})
	html = t.render(c)
	return HttpResponse(html)

def ftp_results(request):
	fields = Field.objects.all()
	resultFiles = os.listdir(path_to_results)
	error = False
	try:
		s = ftplib.FTP(ftp_server, ftp_username, ftp_password) # Connect
		s.cwd(ftp_path)
		for file in resultFiles:
			if file.endswith('.php'):
				path = os.path.join(path_to_results, file)
				f = open(path,'rb')                # file to send
				s.storbinary('STOR '+file, f)         # Send the file

		f.close()                                # Close file and FTP
		s.quit()
	except:
		error = True

	t = get_template('ftp.html')
	c = Context({'fields': fields,
		'error': error
	})
	html = t.render(c)
	return HttpResponse(html)

def save_results(request):
	fields = Field.objects.all()
	createFiles('cr','tt','rr','crit','sprint')
	t = get_template('saved.html')
	c = Context({
		'fields': fields
	})
	html = t.render(c)
	return HttpResponse(html)

def index(request):
	fields = Field.objects.all()
	t = get_template('index.html')
	c = Context({
		'fields': fields
	})
	html = t.render(c)
	return HttpResponse(html)