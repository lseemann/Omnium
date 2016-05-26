from django.db import models

# Create your models here.

class Field(models.Model):
	slug = models.CharField(max_length=8)
	full = models.CharField(max_length=30)
	def __unicode__(self):
		return self.full

class Race(models.Model):
	slug = models.CharField(max_length=8)
	full = models.CharField(max_length=30)
	def __unicode__(self):
		return self.full

class Result(models.Model):
	fname     = models.CharField(max_length=60)
	lname     = models.CharField(max_length=60)
	tt_time   = models.CharField(max_length=60,blank=True, null=True)
	team      = models.CharField(max_length=60)
	usac      = models.PositiveIntegerField(max_length=7,blank=True,null=True)
	field     = models.ForeignKey(Field)
	race      = models.ForeignKey(Race)
	in_omnium = models.BooleanField(default=0)
	place     = models.CharField(max_length=4)
	order     = models.PositiveIntegerField(max_length=3)
	def save(self):
		if self.place.isdigit():
			self.order = self.place
		else:
			self.order = 999
		super(Result, self).save()
	def __unicode__(self):
		return self.lname + ' ' + self.fname + ': ' + self.place + ' in ' + unicode(self.field) + ' ' + unicode(self.race)


class Rider(models.Model):
	fname        = models.CharField(max_length=60)
	lname        = models.CharField(max_length=60)
	team         = models.CharField(max_length=80,blank=True,null=True)
	usac         = models.PositiveIntegerField(max_length=7, unique=True)
	field        = models.ForeignKey(Field)
	cr_place     = models.PositiveIntegerField(max_length=2,blank=True, null=True)
	tt_place     = models.PositiveIntegerField(max_length=4,blank=True, null=True)
	tt_order     = models.PositiveIntegerField(max_length=3,blank=True, null=True,default=999)
	tt_time      = models.CharField(max_length=60,blank=True, null=True)
	rr_place     = models.PositiveIntegerField(max_length=2,blank=True, null=True)
	crit_place   = models.PositiveIntegerField(max_length=2,blank=True, null=True)
	sprint_place = models.PositiveIntegerField(max_length=2,blank=True, null=True)
	omnium       = models.PositiveIntegerField(max_length=4,blank=True,null=True,default=0)
	dq           = models.BooleanField(default=0)
	def cr_points(self):
		points = [0, 34, 30,26,	22,	21,	19,	17,	15,	13,	11,	10,	9, 8,7,	6, 5, 4, 3,	2, 1]
		if (self.cr_place and self.cr_place < len(points)):
			return points[self.cr_place]
		else:
			return 0

	def tt_points(self):
		points = [0, 17, 14, 11, 9, 7, 5, 4, 3, 2, 1]
		if (self.tt_place and self.tt_place< len(points)):
			return points[self.tt_place]
		else:
			return 0

	def rr_points(self):
		points = [0, 37, 31, 28, 24, 22, 20, 18, 16, 14, 12, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
		if (self.rr_place and self.rr_place < len(points)):
			return points[self.rr_place]
		else:
			return 0

	def crit_points(self):
		points = [0, 20, 18, 15, 13, 11, 9, 7, 6, 5, 4, 3, 2, 1]
		if (self.crit_place and self.crit_place < len(points)):
			return points[self.crit_place]
		else:
			return 0

	def sprint_points(self):
		points = [0, 10, 7, 4, 2, 1]
		if (self.sprint_place and self.sprint_place < len(points)):
			return points[self.sprint_place]
		else:
			return 0

	def save(self):
		self.omnium = self.cr_points() + self.tt_points() + self.rr_points() + self.crit_points() + self.sprint_points()
		if self.tt_place and float(self.tt_place): # Test to see if it's a valid number
			self.tt_order = self.tt_place
		else:
			self.tt_order = 999

		super(Rider, self).save()

	def __unicode__(self):
		return self.fname + ' ' + self.lname

	class Meta:
		ordering = ['lname']