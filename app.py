from flask import Flask, request, render_template, flash, redirect, url_for
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from collections import defaultdict, Counter
from datetime import datetime
from urllib.parse import urlparse
import validators
import requests
import string
import math

nltk.download('punkt')

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

# Function to tokenize text into sentences and words
def tokenize_text(text):
    sentences = sent_tokenize(text)  # Sentence tokenization
    words = word_tokenize(text.lower())  # Word tokenization (lowercase for consistency)
    return sentences, words

# Function to calculate word frequency
def calculate_word_frequency(words):
    stop_words = set(nltk.corpus.stopwords.words('english'))  # Load stopwords
    word_freq = defaultdict(int)
    
    for word in words:
        # Filter out punctuation and stopwords
        if word not in string.punctuation and word not in stop_words:
            word_freq[word] += 1

    return word_freq

# Function to rank sentences based on word frequency
def rank_sentences(sentences, word_freq):
    sentence_rank = defaultdict(int)
    
    for i, sentence in enumerate(sentences):
        words_in_sentence = word_tokenize(sentence.lower())
        for word in words_in_sentence:
            if word in word_freq:
                sentence_rank[i] += word_freq[word]
    
    return sentence_rank

# Custom summarization function
def summarize_text(text, max_sentences=5):
    sentences, words = tokenize_text(text)
    word_freq = calculate_word_frequency(words)
    ranked_sentences = rank_sentences(sentences, word_freq)
    
    # Select top-ranked sentences
    top_sentences = sorted(ranked_sentences, key=ranked_sentences.get, reverse=True)[:max_sentences]
    summary = [sentences[i] for i in sorted(top_sentences)]  # Sort to preserve order of sentences in the original text

    return ' '.join(summary)

# Custom sentiment analysis function
def analyze_sentiment(text):
    words = word_tokenize(text.lower())
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

app.secret_key = 'your_secret_key'

if __name__ == '__main__':
    app.run(debug=True)
