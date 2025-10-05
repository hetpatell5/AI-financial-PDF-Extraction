import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import pickle
import os

class CategoryClassifier:
    def __init__(self):
        self.categories = {
            'Food': ['swiggy', 'zomato', 'restaurant', 'cafe', 'food', 'pizza', 'burger', 'dominos', 'mcdonalds', 'kfc'],
            'Shopping': ['amazon', 'flipkart', 'myntra', 'ajio', 'shopping', 'mall', 'store', 'retail', 'market'],
            'Bills': ['electricity', 'water', 'gas', 'bill', 'utility', 'recharge', 'mobile', 'broadband', 'internet'],
            'Transportation': ['uber', 'ola', 'rapido', 'petrol', 'fuel', 'parking', 'toll', 'metro', 'bus', 'train'],
            'Entertainment': ['netflix', 'spotify', 'hotstar', 'prime', 'movie', 'cinema', 'theatre', 'gaming', 'game'],
            'Healthcare': ['hospital', 'pharmacy', 'medical', 'doctor', 'clinic', 'medicine', 'health', 'apollo', 'medplus'],
            'Education': ['school', 'college', 'university', 'course', 'tuition', 'education', 'book', 'fees'],
            'Investment': ['mutual fund', 'sip', 'stock', 'equity', 'investment', 'trading', 'zerodha', 'groww'],
            'Transfer': ['transfer', 'upi', 'imps', 'neft', 'rtgs', 'sent to', 'received from'],
            'ATM': ['atm', 'cash withdrawal', 'withdrawal'],
            'Salary': ['salary', 'wage', 'income', 'payroll'],
            'Other': []
        }
        
        self.model = None
        self.vectorizer = None
        self.model_path = 'models/category_model.pkl'
        self.vectorizer_path = 'models/vectorizer.pkl'
    
    def classify_rule_based(self, description):
        """Classify transaction using rule-based approach"""
        description_lower = description.lower()
        
        # Check each category's keywords
        for category, keywords in self.categories.items():
            if category == 'Other':
                continue
            
            for keyword in keywords:
                if keyword in description_lower:
                    return category
        
        return 'Other'
    
    def classify_transactions(self, transactions):
        """Classify a list of transactions"""
        for transaction in transactions:
            if 'description' in transaction:
                transaction['category'] = self.classify_rule_based(transaction['description'])
            else:
                transaction['category'] = 'Other'
        
        return transactions
    
    def train_ml_model(self, training_data):
        """Train ML model for category classification (optional enhancement)"""
        if not training_data:
            print("No training data provided")
            return
        
        try:
            descriptions = [item['description'] for item in training_data]
            labels = [item['category'] for item in training_data]
            
            # Create TF-IDF vectorizer
            self.vectorizer = TfidfVectorizer(max_features=500, ngram_range=(1, 2))
            X = self.vectorizer.fit_transform(descriptions)
            
            # Train Naive Bayes classifier
            self.model = MultinomialNB()
            self.model.fit(X, labels)
            
            # Save model
            os.makedirs('models', exist_ok=True)
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            with open(self.vectorizer_path, 'wb') as f:
                pickle.dump(self.vectorizer, f)
            
            print("ML model trained and saved successfully")
        except Exception as e:
            print(f"Error training model: {e}")
    
    def load_ml_model(self):
        """Load trained ML model"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.vectorizer_path):
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                with open(self.vectorizer_path, 'rb') as f:
                    self.vectorizer = pickle.load(f)
                print("ML model loaded successfully")
                return True
        except Exception as e:
            print(f"Error loading model: {e}")
        return False
    
    def classify_ml(self, description):
        """Classify using ML model if available"""
        if self.model and self.vectorizer:
            try:
                X = self.vectorizer.transform([description])
                prediction = self.model.predict(X)[0]
                return prediction
            except:
                pass
        
        # Fallback to rule-based
        return self.classify_rule_based(description)
    
    def get_category_stats(self, transactions):
        """Get statistics about categories"""
        stats = {}
        
        for transaction in transactions:
            category = transaction.get('category', 'Other')
            trans_type = transaction.get('type', 'Debit')
            amount = transaction.get('amount', 0)
            
            if category not in stats:
                stats[category] = {'count': 0, 'total_debit': 0, 'total_credit': 0}
            
            stats[category]['count'] += 1
            if trans_type == 'Debit':
                stats[category]['total_debit'] += amount
            else:
                stats[category]['total_credit'] += amount
        
        return stats