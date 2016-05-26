# Omnium
A Django app to manage scoring for a three-day cycling race, designed to serve the Tour of Galena, an omnium race hosted by [XXX Racing-Athletico](http://www.xxxracing.org). It's designed around the quite specific needs of this particular race, so expect to configure around your race’s needs, including fields and results formatting.
## Usage
Omnium is designed to be run locally on Django’s development server.

To run:
```
python manage.py runserver
```
The app will then be available at ```http://127.0.0.1:8000/```, where the user will be given instructions for uploading CSVs of rider rosters and of individual race results.

When results are uploaded, results for omnium participants are stored in the local database and saved locally as HTML files, which the app will optionally upload to a webserver.

Configure the database and a few other paths in `settings.py` and configure FTP credentials and a local path for files in `galena/views.py`.
## Credits
Luke Seemann
