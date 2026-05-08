import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import joblib
import os

# Download NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class ComplaintClassifier:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.model = None
        self.categories = {
            'billing': ['bill', 'payment', 'charge', 'invoice', 'money', 'cost', 'price', 'fee', 'refund'],
            'technical': ['error', 'bug', 'crash', 'not working', 'issue', 'problem', 'failed', 'broken', 'glitch'],
            'service_delay': ['delay', 'waiting', 'late', 'slow', 'pending', 'taking time', 'overdue'],
            'quality': ['poor quality', 'defective', 'damaged', 'not good', 'bad', 'terrible', 'awful'],
            'customer_service': ['rude', 'unhelpful', 'ignored', 'support', 'agent', 'representative', 'customer service']
        }
        
        # Train a simple classifier
        self.train_classifier()
    
    def preprocess_text(self, text):
        """Clean and preprocess text"""
        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        tokens = word_tokenize(text)
        tokens = [t for t in tokens if t not in self.stop_words]
        return ' '.join(tokens)
    
    def train_classifier(self):
        """Train a simple Naive Bayes classifier"""
        training_texts = []
        training_labels = []
        
        for category, keywords in self.categories.items():
            for keyword in keywords:
                training_texts.append(keyword)
                training_labels.append(category)
                # Add variations
                training_texts.append(f"having {keyword} issue")
                training_labels.append(category)
                training_texts.append(f"problem with {keyword}")
                training_labels.append(category)
        
        # Transform texts
        X = self.vectorizer.fit_transform(training_texts)
        y = np.array(training_labels)
        
        # Train model
        self.model = MultinomialNB()
        self.model.fit(X, y)
    
    def calculate_severity(self, text, sentiment):
        """Calculate severity score based on text and sentiment"""
        severity = 0.5  # Default medium severity
        
        # Keywords that increase severity
        high_severity_keywords = ['urgent', 'critical', 'emergency', 'serious', 'severe', 'immediate', 'asap']
        medium_severity_keywords = ['issue', 'problem', 'concern', 'delay']
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in high_severity_keywords):
            severity += 0.4
        elif any(word in text_lower for word in medium_severity_keywords):
            severity += 0.2
        
        # Adjust based on sentiment
        if sentiment == 'negative':
            severity += 0.2
        elif sentiment == 'positive':
            severity -= 0.1
        
        return min(max(severity, 0), 1)  # Keep between 0 and 1
    
    def determine_priority(self, severity_score):
        """Determine priority based on severity score"""
        if severity_score >= 0.7:
            return 'High'
        elif severity_score >= 0.4:
            return 'Medium'
        else:
            return 'Low'
    
    def analyze_sentiment(self, text):
        """Basic sentiment analysis"""
        positive_words = ['good', 'great', 'excellent', 'happy', 'satisfied', 'nice', 'helpful']
        negative_words = ['bad', 'terrible', 'awful', 'angry', 'frustrated', 'upset', 'disappointed', 'worst']
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if negative_count > positive_count:
            return 'negative'
        elif positive_count > negative_count:
            return 'positive'
        else:
            return 'neutral'
    
    def get_department(self, category):
        """Map category to department"""
        department_map = {
            'billing': 'Finance Department',
            'technical': 'IT Support',
            'service_delay': 'Operations Department',
            'quality': 'Quality Assurance',
            'customer_service': 'Customer Relations'
        }
        return department_map.get(category, 'General Support')
    
    def classify_complaint(self, complaint_text):
        """Main classification function"""
        # Preprocess text
        processed_text = self.preprocess_text(complaint_text)
        
        # Classify category
        if self.model:
            X = self.vectorizer.transform([processed_text])
            category = self.model.predict(X)[0]
        else:
            category = 'other'
        
        # Analyze sentiment
        sentiment = self.analyze_sentiment(complaint_text)
        
        # Calculate severity
        severity_score = self.calculate_severity(complaint_text, sentiment)
        
        # Determine priority
        priority = self.determine_priority(severity_score)
        
        # Get department
        department = self.get_department(category)
        
        # Format category name for display
        category_display = category.replace('_', ' ').title()
        
        return {
            'category': category_display,
            'severity_score': severity_score,
            'priority': priority,
            'sentiment': sentiment,
            'department': department
        }
