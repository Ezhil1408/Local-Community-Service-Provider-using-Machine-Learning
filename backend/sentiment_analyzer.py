from textblob import TextBlob
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re


class SentimentAnalyzer:
    """Sentiment analysis for user reviews using TextBlob"""
    
    def __init__(self):
        # Download required NLTK data (run once)
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords', quiet=True)
        
        self.stop_words = set(stopwords.words('english'))
    
    def preprocess_text(self, text):
        """Clean and preprocess text"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and digits
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords
        tokens = [word for word in tokens if word not in self.stop_words]
        
        return ' '.join(tokens)
    
    def analyze_sentiment(self, text):
        """
        Analyze sentiment of text
        Returns: dict with polarity, subjectivity, and label
        """
        if not text or text.strip() == "":
            return {
                'polarity': 0.0,
                'subjectivity': 0.0,
                'sentiment_label': 'Neutral',
                'confidence': 0.0
            }
        
        # Create TextBlob object
        blob = TextBlob(text)
        
        # Get polarity and subjectivity
        polarity = blob.sentiment.polarity  # -1 to 1
        subjectivity = blob.sentiment.subjectivity  # 0 to 1
        
        # Determine sentiment label
        if polarity > 0.1:
            sentiment_label = 'Positive'
        elif polarity < -0.1:
            sentiment_label = 'Negative'
        else:
            sentiment_label = 'Neutral'
        
        # Calculate confidence (absolute polarity)
        confidence = abs(polarity)
        
        return {
            'polarity': round(polarity, 3),
            'subjectivity': round(subjectivity, 3),
            'sentiment_label': sentiment_label,
            'confidence': round(confidence, 3)
        }
    
    def batch_analyze(self, texts):
        """Analyze sentiment for multiple texts"""
        results = []
        for text in texts:
            result = self.analyze_sentiment(text)
            results.append(result)
        return results
    
    def get_sentiment_summary(self, texts):
        """Get summary statistics for a collection of texts"""
        results = self.batch_analyze(texts)
        
        positive_count = sum(1 for r in results if r['sentiment_label'] == 'Positive')
        negative_count = sum(1 for r in results if r['sentiment_label'] == 'Negative')
        neutral_count = sum(1 for r in results if r['sentiment_label'] == 'Neutral')
        
        total = len(results)
        avg_polarity = sum(r['polarity'] for r in results) / total if total > 0 else 0
        avg_subjectivity = sum(r['subjectivity'] for r in results) / total if total > 0 else 0
        
        return {
            'total_reviews': total,
            'positive': positive_count,
            'negative': negative_count,
            'neutral': neutral_count,
            'positive_percentage': round(positive_count / total * 100, 1) if total > 0 else 0,
            'negative_percentage': round(negative_count / total * 100, 1) if total > 0 else 0,
            'neutral_percentage': round(neutral_count / total * 100, 1) if total > 0 else 0,
            'average_polarity': round(avg_polarity, 3),
            'average_subjectivity': round(avg_subjectivity, 3),
            'overall_sentiment': 'Positive' if avg_polarity > 0.1 else 'Negative' if avg_polarity < -0.1 else 'Neutral'
        }
    
    def extract_keywords(self, text, n=5):
        """Extract key phrases from text"""
        blob = TextBlob(text)
        noun_phrases = list(blob.noun_phrases)
        
        # Get word frequency
        words = self.preprocess_text(text).split()
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Only words longer than 3 characters
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:n]
        
        return {
            'noun_phrases': noun_phrases[:n],
            'top_words': [word for word, _ in top_words]
        }


# Example usage and testing
if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    
    # Test reviews
    test_reviews = [
        "Excellent service! Very professional and quick.",
        "Terrible experience. Would not recommend.",
        "Service was okay. Nothing special.",
        "Amazing work! Highly satisfied with the quality.",
        "Poor communication and delayed service."
    ]
    
    print("="*60)
    print("SENTIMENT ANALYSIS TEST")
    print("="*60)
    
    for review in test_reviews:
        result = analyzer.analyze_sentiment(review)
        print(f"\nReview: {review}")
        print(f"Sentiment: {result['sentiment_label']}")
        print(f"Polarity: {result['polarity']}")
        print(f"Confidence: {result['confidence']}")
    
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)
    
    summary = analyzer.get_sentiment_summary(test_reviews)
    print(f"Total Reviews: {summary['total_reviews']}")
    print(f"Positive: {summary['positive']} ({summary['positive_percentage']}%)")
    print(f"Negative: {summary['negative']} ({summary['negative_percentage']}%)")
    print(f"Neutral: {summary['neutral']} ({summary['neutral_percentage']}%)")
    print(f"Overall Sentiment: {summary['overall_sentiment']}")
