import tweepy, datetime, json, io

# tweepy OAuth keys
consumer_key = '3futuKPmSNvjUz1HlZrzBMuqG'
consumer_secret = 'QfG0jyvwOJWZ0BxsLVMvZFWUtxVKGH6LsTsEIUIhV8ZdTVZnFB'
key = '1081355326094434304-xg3gZhpKkZLwCYtan5u0R8ninEe1lN'
secret = 'kl7bo0aWdCI6VyylpCbjVzjkcBSlbIgFUDqd2kK7FxJKj'

# global vars
drivers = [
               ['Lewis', 'Hamilton', '@lewishamilton'], ['Sebastian', 'Vettel', '#SV5'],
               ['Kimi', 'Raikkonen', '@RaikkonenOficia'], ['Max', 'Verstappen', '@max33verstappen'],
               ['Valtteri', 'Bottas', '@valtteribottas'], ['Daniel', 'Ricciardo', '@danielricciardo'],
               ['Nico', 'Hulkenberg', '@HulkHulkenberg'], ['Sergio', 'Perez', '@SChecoPerez'],
               ['Kevin', 'Magnussen', '@kevinmagnussen'], ['Carlos', 'Sainz', '@Carlossainz55'],
               ['Lando', 'Norris', '@LandoNorris'], ['Lance', 'Stroll', '@lance_stroll'],
               ['Charles', 'Leclerc', '@Charles_Leclerc'], ['Romain', 'Grosjean', '@RGrosjean'],
               ['Pierre', 'Gasly', '@PierreGASLY'], ['Antonio', 'Giovinazzi', '@AntoGiovinazzi'],
               ['Alexander', 'Albon', '@alex_albon'], ['Daniil', 'Kvyat', '@kvyatofficial'],
               ['Robert', 'Kubica', '@R_Kubica'], ['George', 'Russell', '@GeorgeRussell63']
           ]
queries = ['#F1', '@F1', '@SkySportsF1']
driver_tally = [0] * len(drivers)
num_tweets_scanned = 0
now = datetime.datetime.now()
cutoff_date = now - datetime.timedelta(days=1)

# return the normalised Levenshtein distance between two strings
def levenshtein_distance(a, b):
    if a == b:
        return 1
    if len(a) < len(b):
        a, b = b, a
    if not a:
        return 0

    previous_row = range(len(b) + 1)
    for i, column1 in enumerate(a):
        current_row = [i + 1]
        for j, column2 in enumerate(b):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (column1 != column2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    # normalise error rate and return result
    norm = max(len(a), len(b))
    return (norm - previous_row[-1])/norm


# read a tweet and find which drivers are in it
def populate_driver_tally(twords):
    global driver_tally
    lev_threshold = 0.7
    temp_tally = [0] * len(drivers)

    for tword in twords:
        for i in range(len(drivers)):
            # do not count the same driver twice in the same tweet
            driver = drivers[i]
            if temp_tally[i] == 0:
                # search word using needles
                if levenshtein_distance(driver[0], tword) > lev_threshold or (
                   levenshtein_distance(driver[1], tword) > lev_threshold) or (
                   levenshtein_distance(driver[2], tword) > lev_threshold):
                    driver_tally[i] += 1
                    temp_tally[i] = 1


def bubble_sort_by_tally(alist):
    for passnum in range(len(alist) - 1, 0, -1):
        for i in range(passnum):
            if alist[i]["Tally"] > alist[i + 1]["Tally"]:
                temp = alist[i]
                alist[i] = alist[i + 1]
                alist[i + 1] = temp
    return alist


def save_tally():
    # create driver dictionaries for json conversion
    drivers_list = []
    for i in range(len(drivers)):
        driver_temp = {"First Name:": drivers[i][0], "Last Name:": drivers[i][1], "Tally": driver_tally[i]}
        drivers_list.append(driver_temp)

    # write JSON file
    sorted_drivers = bubble_sort_by_tally(drivers_list)
    filename = now.strftime("%Y-%m-%d")
    with io.open(filename + '.json', 'w', encoding='utf8') as outfile:
        str_ = json.dumps(sorted_drivers, indent=4, separators=(',', ': '))
        outfile.write(str_)


def scan_tweets(tweets):
    for tweet in tweets:
        # filter tweet dates from yesterday
        if cutoff_date.year == tweet.created_at.year and cutoff_date.month == tweet.created_at.month and tweet.created_at.day >= cutoff_date.day:
            tweet_words = tweet.text.split(' ')
            populate_driver_tally(tweet_words)
    global num_tweets_scanned
    num_tweets_scanned += len(tweets)


def main():
    # access the API
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(key, secret)
    api = tweepy.API(auth)

    # run the search queries
    for query in queries:
        # pagination
        for page in tweepy.Cursor(api.search, q=query, count=100, result_type='recent').pages(3):
            scan_tweets(page)
    save_tally()
    print(driver_tally, 'out of', num_tweets_scanned, 'tweets scanned.')


if __name__ == "__main__":
    main()