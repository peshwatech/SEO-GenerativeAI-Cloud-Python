import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from collections import Counter
import string

# Download required NLTK data files
nltk.download('punkt')
nltk.download('stopwords')

def clean_text(text):
    """
    Clean the input text by removing punctuation and stopwords.
    """
    # Convert to lower case
    text = text.lower()
    
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # Tokenize the text
    words = word_tokenize(text)
    
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    filtered_words = [word for word in words if word not in stop_words]
    
    return filtered_words

def keyword_density(text):
    """
    Calculate the keyword density of the given text.
    """
    words = clean_text(text)
    
    # Count the frequency of each word
    word_counts = Counter(words)
    
    # Total number of words
    total_words = len(words)
    
    # Calculate keyword density
    keyword_density = {word: (count / total_words) * 100 for word, count in word_counts.items()}
    
    return keyword_density

def generate_report(text):
    """
    Generate a keyword density report.
    """
    density = keyword_density(text)
    sorted_density = dict(sorted(density.items(), key=lambda item: item[1], reverse=True))
    
    print("Keyword Density Report:")
    print("=======================")
    for word, density in sorted_density.items():
        print(f"{word}: {density:.2f}%")
    
# Sample text for analysis
sample_text = """
    Search engine optimization (SEO) is the practice of improving the ranking of a website on search engines.
    The higher the ranking, the more likely people are to visit the site.
    SEO involves various techniques, including keyword research, content creation, and link building.
"""

# Generate and print the report
generate_report(sample_text)
