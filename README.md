# Elasticsearch and New York Times

Indexed articles from the New York Time in Elasticsearch. I used the NYT Newswire API to get metadata of recently published articles, crawled the url to get the text of the articles and blogs, and stored the results in Elasticsearch for querying.

Below is an overview of the process:

![Code_Flow_Overview](./Hw12_Overview.png)

## Document Indexing

Below is an example of a news article which was indexed to Elasticsearch

### Original Article

![Original Article](./NYT_article.png)

### Indexed Document

![Indexed Document](./NYT_indexed_doc.png)

## Term Aggregation for Section Field

Elasticsearch can be queried to produce interesting summaries. Below I used the term aggregation on the Section field to determine the percetage of articles in each section.

![Section Distribution](./NYT_SectionTermAgg.png)
