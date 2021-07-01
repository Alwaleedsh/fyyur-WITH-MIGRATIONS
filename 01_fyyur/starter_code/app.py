#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
migrate = Migrate(app, db)
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(500))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    looking_for_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(120))

    #done TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(500))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    looking_for_venues = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(120))


    
class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String)
    day = db.Column(db.String(120))
    time = db.Column(db.String(120))
    artist = db.Column(db.String(120))
    venue = db.Column(db.String(500))

    # DONE TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  city_venues = {}
  city_state = {}

  upcoming_shows, null_expr = get_upcoming_shows_subquery('venue_id')

  venues = Venue.query.with_entities(
    Venue.id, Venue.name,
    Venue.city, Venue.state_id,
    null_expr.label('num_upcoming_shows')
  ).outerjoin(
    upcoming_shows, Venue.id == upcoming_shows.c.venue_id
  ).order_by('city')

  for ven in venues:
      if ven.city not in city_venues:
         city_venues[ven.city] = []
         city_state[ven.city] = ven.state_id
      city_venues[ven.city].append({'id': ven.id,
            'name':ven.name, 'num_upcoming_shows':ven.num_upcoming_shows})
  data =[]
  for city in city_venues:
      data.append({'city': city, 'state': city_state[city], 'venues':city_venues[city]})
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

  upcoming_shows, null_expr = get_upcoming_shows_subquery('venue_id')

  venues = Venue.query.with_entities(
    Venue.id, Venue.name,
    null_expr.label('num_upcoming_shows'),
    db.func.concat(Venue.name, ' ', Venue.city, ', ', Venue.state_id)
  ).outerjoin(
    upcoming_shows, Venue.id == upcoming_shows.c.venue_id
  ).filter(
    db.func.concat(Venue.name, ' ', Venue.city, ', ', Venue.state_id).ilike(
      '%' + request.form.get('search_term', '') + '%'
    )
  )
  response = {'count': venues.count(), 'data': venues}

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>', methods=['GET'])
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: done replace with real venue data from the venues table, using venue_id
  data = Venue.query.options(
    db.joinedload(Venue.shows).
    subqueryload(Show.artist)).get_or_404(venue_id)

  data.past_shows = []
  data.upcoming_shows = []
  past_shows_count, upcoming_shows_count = 0, 0
  attr = ''
  for show in data.shows:
    if show.show_date >= datetime.today():
        upcoming_shows_count += 1
        attr = 'upcoming_shows'
    else:
        past_shows_count += 1
        attr = 'past_shows'

    getattr(data, attr).append({
        'artist_id': show.artist.id,
        'artist_name': show.artist.name,
        'artist_image_link': show.artist.image_link,
        'start_time': show.show_date
    })
  data.past_shows_count = past_shows_count
  data.upcoming_shows_count = upcoming_shows_count
  return render_template('pages/show_venue.html', venue=data)
#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: done insert form data as a new Venue record in the db, instead
  # TODO: done modify data to be the data object returned from db insertion
   form = VenueForm()
   if form.validate_on_submit():
      # on successful db insert, flash success
      error = False
      data = {}
      try:
          venue = Venue()
          form.populate_obj(venue)
          db.session.add(venue)
          db.session.commit()
          data['name'] = venue.name
      except:
          error = True
          db.session.rollback()
          print(sys.exc_info())
          flash('Sorry! it was unable to write data.')
          return render_template('forms/new_venue.html', form=form)
      finally:
          db.session.close()

      if not error:
          flash('Venue ' + data['name'] + ' was successfully listed!')
          return redirect(url_for('venues'))
      else:
       flash('Sorry! please check your data!')
  # TODO: done on unsuccessful db insert, flash an error instead.
   flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
   return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: done Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  venue = Venue.query.get_or_404(venue_id)
  if len(venue.shows):
      flash('Unable to remove the venue on which shows are held!')
      return redirect(url_for('show_venue', venue_id = venue_id))
  data = {}
  data['name'] = venue.name
  try:
    venue.genres = []
    db.session.delete(venue)
    db.session.commit()
    flash('Venue ' + data['name'] + ' has been deleted.')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('Venue ' + data['name'] + ' could not be deleted.')
  finally:
    db.session.close()

  return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: done replace with real data returned from querying the database
  data = Artist.query.order_by('name').all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: done implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  
  upcoming_shows, null_expr = get_upcoming_shows_subquery('artist_id')

  artists = Artist.query.with_entities(
    Artist.id, Artist.name,
    null_expr.label('num_upcoming_shows'),
    db.func.concat(Artist.name, ' ', Artist.city, ', ', Artist.state_id)
  ).outerjoin(
    upcoming_shows, Artist.id == upcoming_shows.c.artist_id
  ).filter(
    db.func.concat(Artist.name, ' ', Artist.city, ', ', Artist.state_id).ilike(
      '%' + request.form.get('search_term', '') + '%'
    )
  )

  response = {'count': artists.count(), 'data': artists}

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: done replace with real artist data from the artist table, using artist_id
 
  data = Artist.query.get_or_404(artist_id)

  data = Artist.query.options(
    db.joinedload(Artist.shows).
    subqueryload(Show.venue)).get_or_404(artist_id)

  data.past_shows = []
  data.upcoming_shows = []
  past_shows_count, upcoming_shows_count = 0, 0
  attr = ''
  for show in data.shows:
    if show.show_date >= datetime.today():
        upcoming_shows_count += 1
        attr = 'upcoming_shows'
    else:
        past_shows_count += 1
        attr = 'past_shows'

    getattr(data, attr).append({
        'venue_id': show.venue.id,
        'venue_name': show.venue.name,
        'venue_image_link': show.venue.image_link,
        'start_time': show.show_date
    })
  data.past_shows_count = past_shows_count
  data.upcoming_shows_count = upcoming_shows_count

  return render_template('pages/show_artist.html', artist=data)
#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  # TODO: done populate form with fields from artist with ID <artist_id>
  artist = Artist.query.get_or_404(artist_id)
  form = ArtistForm(obj=artist)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: done take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
   form = ArtistForm()
   if form.validate_on_submit():
       try:
           artist = Artist()
           form.populate_obj(artist)
           db.session.commit()
           flash('Artist ' + request.form['name'] + ' was successfully updated!')
       except:
           db.session.rollback()
           print(sys.exc_info())
           flash('Sorry! it was unable to write data.')
       finally:
           db.session.close()
   else:
       flash('Sorry! please check your data.')
   return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  # TODO: done populate form with values from venue with ID <venue_id>
  venue = Venue.query.get_or_404(venue_id)
  form = VenueForm(obj=venue)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: done take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm()
  if form.validate_on_submit():
      error = False
      data = {}
      try:
          venue = Venue()
          form.populate_obj(venue)
          db.session.commit()
          data['name'] = venue.name
      except:
          error = True
          db.session.rollback()
          print(sys.exc_info())
          flash('Sorry! it was unable to write data.')
      finally:
          db.session.close()

      if not error:
          flash('Venue ' + data['name'] + ' was successfully updated!')
  else:
      flash('Sorry! Please check your data.')
  return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: done insert form data as a new Venue record in the db, instead
  # TODO: done modify data to be the data object returned from db insertion
  form = ArtistForm()
  data = {}
  if form.validate_on_submit():
      try:
          artist = Artist()
          form.populate_obj(artist)
          db.session.add(artist)
          db.session.commit()
          data['name'] = artist.name
      except:
          db.session.rollback()
          print(sys.exc_info())
          flash('Sorry! it was unable to write data.')
          return render_template('forms/new_artist.html', form=form)
      finally:
          db.session.close()

      flash('Artist ' + data['name'] + ' was successfully listed!')
      return redirect(url_for('artists'))
  else:
      flash('Sorry! please check your data.')
  # on successful db insert, flash success
  flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: done on unsuccessful db insert, flash an error instead.
  flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: done replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data = Show.query.order_by('show_date').all()
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
   form = ShowForm()
   if form.validate_on_submit():
      try:
          show = Show()
          form.populate_obj(show)
          db.session.add(show)
          db.session.commit()
          flash('Show has been successfully listed.')
      except:
          db.session.rollback()
          print(sys.exc_info())
          flash('Sorry! Unable to write the data.')
          return render_template('forms/new_show.html', form=form)
      finally:
          db.session.close()

      return redirect(url_for('shows'))
   else:
      flash('Please check the data')
  # on successful db insert, flash success
   flash('Show was successfully listed!')
  # TODO: Done on unsuccessful db insert, flash an error instead.
   flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
   return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
