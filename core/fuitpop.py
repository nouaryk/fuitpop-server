#   Author: Brendon McBain
#   Description: Twitter driver popularity server script
#   Dependencies: tweepy, dotenv, textblob, python 3.6

import tweepy, datetime, json, io, urllib.request, unicodedata, os
from dotenv import load_dotenv
from textblob import TextBlob

# tweepy OAuth keys from .env
load_dotenv()
consumer_key = os.getenv('CONSUMER_KEY')
consumer_secret = os.getenv('CONSUMER_SECRET')
key = os.getenv('ACCESS_TOKEN')
secret = os.getenv('ACCESS_TOKEN_SECRET')

# global vars
queries = ['#F1']
num_query_pages = 44
num_tweets_scanned = 0

drivers = {}
tracks = {}
driver_tally = [0]
driver_polarity = [0]

now = datetime.datetime.now()
cutoff_date = now - datetime.timedelta(days=1)


# remove accents from input string
def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u''.join([c for c in nfkd_form
                    if not unicodedata.combining(c)])


# return the normalised Levenshtein distance between two strings
def levenshtein_distance(a, b):
    if a == b:
        return 1
    if len(a) < len(b):
        (a, b) = (b, a)
    if not a:
        return 0

    previous_row = range(len(b) + 1)
    for (i, column1) in enumerate(a):
        current_row = [i + 1]
        for (j, column2) in enumerate(b):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (column1 != column2)
            current_row.append(min(insertions, deletions,
                               substitutions))
        previous_row = current_row

    # normalise error rate and return result
    norm = max(len(a), len(b))
    return (norm - previous_row[-1]) / norm


# read a tweet and find which drivers are in it and its polarity
def populate_driver_tally(tweet):
    global driver_tally, driver_polarity
    lev_threshold = 0.65
    temp_tally = [0] * len(drivers)
    blob = TextBlob(tweet.text)
    twords = blob.words
    polarity = (blob.sentiment.polarity + 1)/2     # normalised polarity

    for tword in twords:
        for i in range(len(drivers)):

            # do not count the same driver twice in the same tweet
            driver = drivers[i]
            if temp_tally[i] == 0:

                # search word using needles
                firstName = remove_accents(driver['givenName'])
                lastName = remove_accents(driver['familyName'])

                if levenshtein_distance(firstName, tword) > lev_threshold \
                    or levenshtein_distance(lastName, tword) > lev_threshold \
                    or levenshtein_distance(firstName + lastName, tword) > lev_threshold \
                    or levenshtein_distance(driver['code'], tword) > lev_threshold \
                    or levenshtein_distance(driver['familyName'], tword) > lev_threshold:
                    driver_tally[i] += 1
                    driver_polarity[i] = (driver_polarity[i] + polarity)/2      # update polarity by averaging
                    temp_tally[i] = 1


def bubble_sort_by(alist, key):
    for passnum in range(len(alist) - 1, 0, -1):
        for i in range(passnum):
            if alist[i][key] < alist[i + 1][key]:
                temp = alist[i]
                alist[i] = alist[i + 1]
                alist[i + 1] = temp
    return alist


def save_tally():

    # create driver dictionaries for json conversion
    drivers_list = []
    tally_sum = sum(driver_tally)
    for i in range(len(drivers)):
        drivers_list.append({
            'firstName': remove_accents(drivers[i]['givenName']),
            'lastName': remove_accents(drivers[i]['familyName']),
            'popularity': driver_tally[i]/tally_sum,
            'code': drivers[i]['code'],
            'polarity': round(driver_polarity[i], 2)
            })

    # write JSON file
    sorted_drivers = bubble_sort_by(drivers_list, 'popularity')
    wrapped_json = {'drivers': sorted_drivers}
    filename = now.strftime('%Y-%m-%d')

    with io.open('data/' + filename + '.json', 'w', encoding='utf8') as outfile:
        str_ = json.dumps(wrapped_json, indent=4, separators=(',',  ': '))
        outfile.write(str_)

# scan tweets filtered from the same time yesterday
def scan_tweets(tweets):
    for tweet in tweets:

        # filter tweet dates from yesterday
        if cutoff_date.year == tweet.created_at.year \
            and cutoff_date.month == tweet.created_at.month \
            and tweet.created_at.day >= cutoff_date.day:
            populate_driver_tally(tweet)
    global num_tweets_scanned
    num_tweets_scanned += len(tweets)

# get current drivers from Ergast API
def get_drivers():
    global drivers
    data = ergast_json_request('http://ergast.com/api/f1/' + str(now.year) + '/drivers.json')
    drivers = data['MRData']['DriverTable']['Drivers']

# get current tracks and year calendar from Ergast API
def get_tracks():
    global tracks, queries
    data = ergast_json_request('http://ergast.com/api/f1/' + str(now.year) + '.json')
    tracks = data['MRData']['RaceTable']['Races']

    # append grand prix hashtags to queries
    for track in tracks:
        raceName = track['raceName']
        t = raceName.split(' ')[:-2]
        hashtag = '#' + ''.join(t) + 'GP'
        queries.append(hashtag)

    # cache the API data for web use
    with io.open('data/Calendar_' + str(now.year) + '.json', 'w',
                        encoding='utf8') as outfile:
        str_ = json.dumps(data, indent=4, separators=(',', ': '))
        outfile.write(str_)


# request data from Ergast API with multiple tries in case of timeouts
def ergast_json_request(addr):
    for attempt in range(10):
        try:
            with urllib.request.urlopen(addr) as url:
                return json.loads(url.read().decode())
        except (urllib.request.HTTPError, urllib.request.URLError):
            pass
    return {}


# update the twitter championship in the case yesterday was a race day
def update_championship():

    # create championship points placeholder
    drivers_championship = []
    points_system = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
    last_race_data = {'raceName': [], 'drivers': []}

    for driver in drivers:
        drivers_championship.insert(0,
                                    {'firstName': remove_accents(driver['givenName']),
                                    'lastName': remove_accents(driver['familyName']),
                                     'points': 0})

    # calculate championship points using currently stored data
    for track in tracks:

        # check if data exists the day after a grand prix
        targetDate = datetime.datetime.strptime(track['date'], '%Y-%m-%d') + datetime.timedelta(days=1)
        try:
            filename = 'data/' + datetime.datetime.strftime(targetDate, '%Y-%m-%d') + '.json'
            with open(filename, 'r') as f:
                json_data = json.load(f)
                gp_driver_tally = json_data['drivers']

                # update last race data
                last_race_data['raceName'] = track['raceName']
                last_race_data['drivers'] = gp_driver_tally
        except FileNotFoundError:
            break       # no more grand prix data after this date

        # update championship placeholder points
        for x in range(len(points_system)):

            # find the driver index
            ind = 0
            for y in range(len(drivers_championship)):
                if gp_driver_tally[x]['firstName'] == drivers_championship[y]['firstName']:
                    ind = y

            # update points
            points_dict = {'Points': points_system[x] + drivers_championship[ind]['points']}
            drivers_championship[ind].update(points_dict)

    # save new championship
    sorted_wdc = bubble_sort_by(drivers_championship, 'points')
    with io.open('data/Championship_' + str(now.year) + '.json', 'w',
                 encoding='utf8') as outfile:
        str_ = json.dumps(sorted_wdc, indent=4, separators=(',', ': '))
        outfile.write(str_)

    # save last race data
    with io.open('data/Last_Race.json', 'w',
                encoding='utf8') as outfile:
        str_ = json.dumps(last_race_data, indent=4, separators=(',', ': '))
        outfile.write(str_)


def main():

    # access the API
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(key, secret)
    api = tweepy.API(auth)

    # get the drivers to be searched, and race calendar for querying
    get_drivers()
    get_tracks()

    global driver_tally, driver_polarity
    driver_tally = [0] * len(drivers)
    driver_polarity = [0.5] * len(drivers)      # start with neutral polarity

    if len(drivers) == 0 or len(tracks) == 0:
        print('Ergast API did not return any data.')
        return      # empty API data, so do nothing

    # run the search queries
    print('Scanning tweets...')
    query = ' OR '.join(queries)  # OR operator for tags
    for page in tweepy.Cursor(api.search, q=query, count=100, result_type='recent').pages(num_query_pages):
        scan_tweets(page)

    save_tally()
    update_championship()
    print(num_tweets_scanned, 'tweets have been scanned.')

    # update twitter status
    try:
        api.update_status('The daily rank data for ' + now.strftime('%Y-%m-%d') + ' has been updated.')
    except tweepy.error.TweepError:
        pass


if __name__ == '__main__':
    main()