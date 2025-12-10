import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns
import joblib


class ReliabilityClassifier:
    """ML classifier for provider reliability prediction"""
    
    def __init__(self):
        self.rf_model = None
        self.lr_model = None
        self.scaler = StandardScaler()
        self.feature_names = ['experience_years', 'rating', 'total_jobs', 
                             'completion_rate', 'response_time', 'verified']
        self.label_map = {
            0: 'Low Reliability',
            1: 'Moderately Reliable',
            2: 'Highly Reliable'
        }
        
    def prepare_data(self, df):
        """Prepare data for training"""
        X = df[self.feature_names].values
        y = df['reliability_label'].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Check if stratification is possible
        unique, counts = np.unique(y, return_counts=True)
        min_samples = counts.min()
        
        if min_samples < 2:
            # Don't use stratification if any class has less than 2 samples
            return train_test_split(X_scaled, y, test_size=0.2, random_state=42)
        else:
            return train_test_split(X_scaled, y, test_size=0.2, random_state=42, stratify=y)
    
    def train_models(self, X_train, y_train):
        """Train Random Forest and Logistic Regression models"""
        print("Training Random Forest Classifier...")
        self.rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42,
            class_weight='balanced'
        )
        self.rf_model.fit(X_train, y_train)
        
        print("Training Logistic Regression Classifier...")
        self.lr_model = LogisticRegression(
            max_iter=1000,
            random_state=42,
            class_weight='balanced',
            multi_class='multinomial'
        )
        self.lr_model.fit(X_train, y_train)
        
    def evaluate_models(self, X_test, y_test):
        """Evaluate both models and generate reports"""
        print("\n" + "="*60)
        print("RANDOM FOREST EVALUATION")
        print("="*60)
        
        rf_pred = self.rf_model.predict(X_test)
        rf_accuracy = accuracy_score(y_test, rf_pred)
        print(f"Accuracy: {rf_accuracy:.4f}")
        print("\nClassification Report:")
        print(classification_report(y_test, rf_pred, zero_division=0))
        
        print("\n" + "="*60)
        print("LOGISTIC REGRESSION EVALUATION")
        print("="*60)
        
        lr_pred = self.lr_model.predict(X_test)
        lr_accuracy = accuracy_score(y_test, lr_pred)
        print(f"Accuracy: {lr_accuracy:.4f}")
        print("\nClassification Report:")
        print(classification_report(y_test, lr_pred, zero_division=0))
        
        # Generate confusion matrices
        self._plot_confusion_matrices(y_test, rf_pred, lr_pred)
        
        # Feature importance for Random Forest
        self._plot_feature_importance()
        
        return {
            'rf_accuracy': rf_accuracy,
            'lr_accuracy': lr_accuracy,
            'rf_predictions': rf_pred,
            'lr_predictions': lr_pred
        }
    
    def _plot_confusion_matrices(self, y_test, rf_pred, lr_pred):
        """Plot confusion matrices for both models"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Random Forest
        cm_rf = confusion_matrix(y_test, rf_pred)
        sns.heatmap(cm_rf, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=['Low', 'Moderate', 'High'],
                   yticklabels=['Low', 'Moderate', 'High'],
                   ax=axes[0])
        axes[0].set_title('Random Forest - Confusion Matrix')
        axes[0].set_ylabel('True Label')
        axes[0].set_xlabel('Predicted Label')
        
        # Logistic Regression
        cm_lr = confusion_matrix(y_test, lr_pred)
        sns.heatmap(cm_lr, annot=True, fmt='d', cmap='Oranges',
                   xticklabels=['Low', 'Moderate', 'High'],
                   yticklabels=['Low', 'Moderate', 'High'],
                   ax=axes[1])
        axes[1].set_title('Logistic Regression - Confusion Matrix')
        axes[1].set_ylabel('True Label')
        axes[1].set_xlabel('Predicted Label')
        
        plt.tight_layout()
        plt.savefig('confusion_matrices.png', dpi=300, bbox_inches='tight')
        print("\n✓ Confusion matrices saved to confusion_matrices.png")
        
    def _plot_feature_importance(self):
        """Plot feature importance from Random Forest"""
        importances = self.rf_model.feature_importances_
        indices = np.argsort(importances)[::-1]
        
        plt.figure(figsize=(10, 6))
        plt.bar(range(len(importances)), importances[indices], color='steelblue')
        plt.xticks(range(len(importances)), 
                  [self.feature_names[i] for i in indices], rotation=45, ha='right')
        plt.xlabel('Features')
        plt.ylabel('Importance')
        plt.title('Feature Importance - Random Forest')
        plt.tight_layout()
        plt.savefig('feature_importance.png', dpi=300, bbox_inches='tight')
        print("✓ Feature importance plot saved to feature_importance.png")
        
    def predict(self, provider_features, model_type='rf'):
        """Predict reliability for new provider"""
        features = np.array([[
            provider_features.get('experience_years', 0),
            provider_features.get('rating', 0),
            provider_features.get('total_jobs', 0),
            provider_features.get('completion_rate', 0),
            provider_features.get('response_time', 0),
            provider_features.get('verified', 0)
        ]])
        
        features_scaled = self.scaler.transform(features)
        
        if model_type == 'rf':
            prediction = self.rf_model.predict(features_scaled)[0]
            probability = self.rf_model.predict_proba(features_scaled)[0]
        else:
            prediction = self.lr_model.predict(features_scaled)[0]
            probability = self.lr_model.predict_proba(features_scaled)[0]
        
        return {
            'reliability': self.label_map[prediction],
            'confidence': float(max(probability)),
            'probabilities': {
                'Low Reliability': float(probability[0]),
                'Moderately Reliable': float(probability[1]),
                'Highly Reliable': float(probability[2])
            }
        }
    
    def save_models(self, directory='models'):
        """Save trained models and scaler"""
        os.makedirs(directory, exist_ok=True)
        
        joblib.dump(self.rf_model, os.path.join(directory, 'rf_classifier.pkl'))
        joblib.dump(self.lr_model, os.path.join(directory, 'lr_classifier.pkl'))
        joblib.dump(self.scaler, os.path.join(directory, 'scaler.pkl'))
        
        print(f"\n✓ Models saved to {directory}/")
        
    def load_models(self, directory='models'):
        """Load trained models and scaler"""
        self.rf_model = joblib.load(os.path.join(directory, 'rf_classifier.pkl'))
        self.lr_model = joblib.load(os.path.join(directory, 'lr_classifier.pkl'))
        self.scaler = joblib.load(os.path.join(directory, 'scaler.pkl'))
        
        print(f"✓ Models loaded from {directory}/")


def train_and_save_models(data_file='training_data.csv'):
    """Main function to train and save models"""
    print("Loading training data...")
    df = pd.read_csv(data_file)
    
    print(f"Dataset shape: {df.shape}")
    print(f"\nReliability distribution:")
    print(df['reliability'].value_counts())
    
    classifier = ReliabilityClassifier()
    
    print("\nPreparing data...")
    X_train, X_test, y_train, y_test = classifier.prepare_data(df)
    
    print(f"Training set: {X_train.shape[0]} samples")
    print(f"Test set: {X_test.shape[0]} samples")
    
    classifier.train_models(X_train, y_train)
    
    print("\nEvaluating models...")
    results = classifier.evaluate_models(X_test, y_test)
    
    classifier.save_models()
    
    return classifier, results


if __name__ == "__main__":
    classifier, results = train_and_save_models()
    
    # Test prediction
    print("\n" + "="*60)
    print("TESTING PREDICTION")
    print("="*60)
    
    test_provider = {
        'experience_years': 10,
        'rating': 4.8,
        'total_jobs': 250,
        'completion_rate': 0.95,
        'response_time': 2.5,
        'verified': 1
    }
    
    prediction = classifier.predict(test_provider, model_type='rf')
    print(f"\nTest Provider Features: {test_provider}")
    print(f"Predicted Reliability: {prediction['reliability']}")
    print(f"Confidence: {prediction['confidence']:.2%}")
    print(f"Probabilities: {prediction['probabilities']}")
