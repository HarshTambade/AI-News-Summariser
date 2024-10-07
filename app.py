from flask import Flask, request, render_template, flash, redirect, url_for
from collections import defaultdict
from datetime import datetime
from urllib.parse import urlparse
import validators
import requests
import string
import re

app = Flask(__name__)

# Load a basic sentiment lexicon
positive_words = set(["good", "happy", "positive", "fortunate", "correct", "superior", "great", "excellent", "fantastic", "wonderful", "pleasure"])
negative_words = set(["bad", "sad", "negative", "unfortunate", "wrong", "inferior", "terrible", "awful", "horrible", "pain"])

# Function to extract website name
def get_website_name(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    if domain.startswith("www."):
        domain = domain[4:]
    return domain

# Custom function to split text into sentences
def custom_sentence_tokenize(text):
    # Simple regex for sentence splitting
    sentences = re.split(r'(?<=[.!?]) +', text)
    return sentences

# Custom function to split text into words
def custom_word_tokenize(text):
    # Remove punctuation and split by whitespace
    words = re.findall(r'\b\w+\b', text.lower())
    return words

# Function to calculate word frequency
def calculate_word_frequency(words):
    stop_words = set(["a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "as", "at",
                      "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can", "could",
                      "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", "each",
                      "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having",
                      "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself",
                      "his", "how", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
                      "its", "itself", "just", "ll", "me", "might", "mightn't", "more", "most", "must", "mustn't",
                      "my", "myself", "need", "needn't", "no", "nor", "not", "of", "off", "on", "once", "only",
                      "or", "other", "our", "ours", "ourselves", "out", "over", "own", "re", "same", "shan't", "she",
                      "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "t", "than", "that",
                      "that's", "the", "their", "theirs", "them", "themselves", "then", "there", "there's", "these",
                      "they", "they'd", "they'll", "they're", "they've", "this", "those", "through", "to", "too", "under",
                      "until", "up", "ve", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
                      "weren't", "what", "what's", "when", "where", "where's", "which", "while", "who", "who's", "whom",
                      "why", "will", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've",
                      "your", "yours", "yourself", "yourselves"])
    
    word_freq = defaultdict(int)
    
    for word in words:
        # Filter out stopwords
        if word not in stop_words:
            word_freq[word] += 1

    return word_freq

# Function to rank sentences based on word frequency
def rank_sentences(sentences, word_freq):
    sentence_rank = defaultdict(int)
    
    for i, sentence in enumerate(sentences):
        words_in_sentence = custom_word_tokenize(sentence)
        for word in words_in_sentence:
            if word in word_freq:
                sentence_rank[i] += word_freq[word]
    
    return sentence_rank

# Custom summarization function
def summarize_text(text, max_sentences=5):
    sentences = custom_sentence_tokenize(text)
    words = custom_word_tokenize(text)
    word_freq = calculate_word_frequency(words)
    ranked_sentences = rank_sentences(sentences, word_freq)
    
    # Select top-ranked sentences
    top_sentences = sorted(ranked_sentences, key=ranked_sentences.get, reverse=True)[:max_sentences]
    summary = [sentences[i] for i in sorted(top_sentences)]  # Sort to preserve order of sentences in the original text

    return ' '.join(summary)

# Custom sentiment analysis function
def analyze_sentiment(text):
    words = custom_word_tokenize(text)
    positive_count = sum(1 for word in words if word in positive_words)
    negative_count = sum(1 for word in words if word in negative_words)

    if positive_count > negative_count:
        return 'positive 😊'
    elif negative_count > positive_count:
        return 'negative 😟'
    else:
        return 'neutral 😐'

# Main route for the app
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        # Validate the URL
        if not validators.url(url):
            flash('Please enter a valid URL.')
            return redirect(url_for('index'))

        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.RequestException:
            flash('Failed to download the content of the URL.')
            return redirect(url_for('index'))

        # Simple scraping of text content
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        article_text = ' '.join([p.get_text() for p in soup.find_all('p')])

        if not article_text.strip():
            flash('No content found on the page.')
            return redirect(url_for('index'))

        # Title extraction
        title = soup.title.string if soup.title else "No Title"
        
        # Custom text summarization
        summary = summarize_text(article_text, max_sentences=5)

        # Custom sentiment analysis
        sentiment = analyze_sentiment(article_text)

        # Placeholder values for author and image (since we're not using `newspaper` library)
        authors = get_website_name(url)
        publish_date = datetime.now().strftime('%B %d, %Y')
        top_image = url_for('static', filename='default_image.png')

        return render_template('index.html', title=title, authors=authors, publish_date=publish_date, summary=summary, top_image=top_image, sentiment=sentiment)

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
