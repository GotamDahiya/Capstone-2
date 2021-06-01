import pandas as pd
import re, tweepy, json, argparse, os

from tweepy import OAuthHandler
from textblob import TextBlob

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

class DownloadTwitterData:

    def __init__(self, key_json):
        self.api_key = key_json['apikey']
        self.api_key_secret = key_json['apikeysecret']
        self.access_token = key_json['accesstoken']
        self.access_token_secret = key_json['accesstokensecret']
        pass

    def connectingTwitter(self):
        try:
            auth = OAuthHandler(self.api_key, self.api_key_secret)
            auth.set_access_token(self.access_token, self.access_token_secret)

            api = tweepy.API(auth)
            return api
        except:
            print("Error. Connection Failed.")
        pass

    def cleanTweet(self, tweet):
        
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())
        pass

    def removeStopwords(self, tweet):

        tweet_tokens = word_tokenize(tweet)
        tweet_without_stopwords = [word for word in tweet_tokens if word not in stopwords.words()]

        return ' '.join(tweet_without_stopwords)
        pass
    def getSentiment(self, tweet):

        analysis = TextBlob(tweet)
        return analysis.sentiment.polarity
        pass

    def getTweets(self, api, query, count):

        self.connectingTwitter()
        query += " -filter:retweets"
        tweets = []
        try:
            fetched_tweets = tweepy.Cursor(api.search, 
                        q=query,
                        lang='en', 
                        count=count,
                        since_id=None,
                        max_id=None,
                        tweet_mode='extended',
                        exclude_replies=True,
                        contributor_details=False,
                        include_entities=False
                        ).items(count)
            # fetched_tweets = api.search(q=query, count=count, since_id=None, max_id=None)

            for i, tweet in enumerate(fetched_tweets):
                print("\r{}".format(i+1), end="")
                parsed_tweet = {}
                clean_tweet = self.cleanTweet(tweet.full_text)
                
                if len(clean_tweet.split(' ')) < 3:
                    continue
                parsed_tweet['Clean Tweet'] = clean_tweet
                parsed_tweet['Sentiment'] = self.getSentiment(clean_tweet)

                if tweet.retweet_count > 0:
                    if parsed_tweet not in tweets:
                        tweets.append(parsed_tweet)
                else:
                    tweets.append(parsed_tweet)
                pass
            print() 
            return tweets

        except tweepy.TweepError as e:
            print(e)
        pass

if __name__ == "__main__":

    ap = argparse.ArgumentParser()
    ap.add_argument("-j", "--json", required=True,
        help="Path to JSON file containing the keys")
    ap.add_argument("-a", "--account",default='*', required=False,
        help="Comma separated list of account names")
    ap.add_argument("-n", "--number", required=True,
        help="Comma separated list of number of tweets per account name")
    ap.add_argument("-o", "--output", required=True,
        help="Path to output CSV")
    args = vars(ap.parse_args())

    with open(args['json'], 'r') as in_file:
        key_json = json.load(in_file)
        in_file.close()
        pass

    twitter_data = DownloadTwitterData(key_json)
    print("[INFO] Connecting to twitter.")
    api = twitter_data.connectingTwitter()

    account_name_number = [[acc_n, int(n)] for acc_n, n in zip(args["account"].split(','), args["number"].split(','))]

    if os.path.exists(args["output"]):
        print("[INFO] Reading CSV.")
        all_tweets = pd.read_csv(args["output"])
    else:
        print("[INFO] Creating dataframe.")
        all_tweets = pd.DataFrame(columns=['Clean Tweet', 'Sentiment'])
    
    for query, count in account_name_number:
        print("[INFO] {} : {}".format(query, count))
        downloaded_tweets = twitter_data.getTweets(api, query, count)
        all_tweets = all_tweets.append(downloaded_tweets, ignore_index=True, sort=False)
        print("[INFO] finished user")
        pass

    print("[INFO] Storing all tweets dataframe.")
    all_tweets.to_csv(args["output"], index=False)
    print("[INFO] Finished storing all tweets dataframe.")    