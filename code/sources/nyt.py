import requests
import sys
import json
import ratelim
import time
import datetime
from bs4 import BeautifulSoup

class IngestNYT:
    """Ingest data from New York Times Newswire API"""
    def __init__(self, config):
        
        # Configurations variables        
        self.api_key = config['api_key']
        self.host = config['host']
        self.port = config['port']
        
        # NYT Newswire API variables
        self.dayRateLimit = 5000
        self.docsPerPage = 20
        self.ndocs = None
        self.offset = 0
        self.seen = set()
        
        # Elasticsearch (es) variables
        self.elasticsearch = 'http://%s:%s/nytimes/'%(self.host, self.port)
        self.total = 0
        self.count = {}

    
    def start_collection(self):
        '''Start main collection process'''
        
        while(True):
            self.__run()
    
    
    # 5000 call per day (seconds per day = 24h*60min*60sec = 86400)
    @ratelim.greedy(5000, 86400)
    def __run(self):
        '''Wrapper for collection process to stay within daily rate limit'''
        
        results = self.__get_20articles(self.offset)
        
        if results == None:
            pass
        else:
            # Increase offset for NYT API
            self.offset += self.docsPerPage
            if self.offset > self.ndocs:
                self.offset = 0
            
            for doc in results:
                already_exists = self.__exists(doc)
                
                if already_exists == True:
                    # Document already seen and added to index
                    pass
                else:
                    # Add document to list of previously seen documents
                    self.seen.add(doc['url'])
                    # Format document to be added to index
                    self.__parse(doc)
                    # Add the full text to the document
                    self.__get_text(doc)
                    # Add to index
                    self.__write(doc)
    
    
    # 8 calls per second   
    @ratelim.patient(8, 1)
    def __get_20articles(self, offset):
        '''Call the NYT Newswire API to get 20 articles with given offset'''
        
        #### Define url for http request
        url = 'http://api.nytimes.com/svc/news/v3/content/nyt/all/.json?offset=%d&api-key=%s'%(offset, self.api_key)
        response = requests.get(url)
        if response.status_code <> 200:
            print "--- ERROR in API CALL ---"
            print response.status_code
            #print response.headers
            print "Start 6h sleep at:\t",datetime.datetime.now().ctime()
            time.sleep(21600)
            return None
            
        else:
            self.ndocs = response.json()['num_results']
            return response.json()['results']

    def __exists(self, document):
        if document['url'] in self.seen:
            return True
        elif self.total > 0:
            query = {"query": { "match_phrase": { "url": document['url'] } }, "_source": ["_id", "url"]}
            query = json.dumps(query)
            
            url = self.elasticsearch + "_search"
            response = requests.post(url, data=query)
            
            if response.status_code == 200:
                if response.json()['hits']['total'] >= 1:
                    return True
                else:
                    return False
            else:
                print "--- ERROR in EXISTS ---"
                print response.status_code
                print document['url'] 
                return True
        else:
            return False

        
    def __parse(self, data):
        '''Parse documents for storage'''        
        # Remove fields not wanted in storage
        data.pop('related_urls', None)
        data.pop('multimedia', None)


    def __get_text(self, document):
        '''Get the full article text'''  
        # Get full text content of article
        clean_url = document['url'].replace('\\', '')
        response = requests.get(clean_url)
        soup = BeautifulSoup(response.text, 'html.parser')        
        text = '\n'.join(p.text for p in soup.find_all("p", class_="story-body-text"))
        
        # Add text to document        
        document.setdefault('text', text)
        
        
    def __write(self, document):
        '''Wite document to elasticsearch'''
        
        try:
            item_type = document['item_type']
        except:
            item_type = "Article"
        
        doc_id = str(self.count.setdefault(item_type,0) + 1)
        
        url = self.elasticsearch + item_type + "/" + doc_id

        item = json.dumps(document)
        response = requests.post(url, data=item)
        
        if response.status_code == 201:
            self.total += 1
            self.count[item_type] += 1
            if (self.total % 25) <> 0:
                sys.stdout.write('.') # write a record indicator to stdout
                sys.stdout.flush()
            else:
                other = self.total - self.count['Article'] - self.count['Blog']
                print '|\tTotal: {:,}, Articles: {:,}, Blogs: {:,}, Other: {:,}'.format(self.total, self.count['Article'], self.count['Blog'], other)
        else:
            print ("--- FAIL TO WRITE---")
