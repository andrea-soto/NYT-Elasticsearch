import argparse
import ConfigParser

from sources.nyt import IngestNYT

def main(config):
    
    nyt_config = dict(config.items('NYT'))

    ingest = IngestNYT(nyt_config)
    ingest.start_collection()

if __name__ == "__main__":
    '''Application to collect article data from NYT'''
    parser = argparse.ArgumentParser(
        description = "Hw12, W251, Elasticsearch - Crawl NYT articles and store them in elasticsearch" )
    parser.add_argument(
        '--config', help = "path to configuration file", required = True )
        
    args = parser.parse_args()
    config = ConfigParser.ConfigParser()
    config.read(args.config)
    
    main(config)

