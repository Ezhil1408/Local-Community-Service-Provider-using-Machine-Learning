import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from math import radians, sin, cos, sqrt, atan2
import joblib
import os


class HybridRecommender:
    """Hybrid recommendation system combining collaborative and content-based filtering"""
    
    def __init__(self):
        self.user_provider_matrix = None
        self.provider_features = None
        self.similarity_matrix = None
        
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points using Haversine formula (in km)"""
        R = 6371  # Earth's radius in kilometers
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = R * c
        
        return distance
    
    def build_user_provider_matrix(self, interactions):
        """Build user-provider interaction matrix for collaborative filtering"""
        # Create interaction scores
        interaction_weights = {
            'view': 1,
            'contact': 2,
            'hire': 4,
            'favorite': 3
        }
        
        data = []
        for interaction in interactions:
            weight = interaction_weights.get(interaction.interaction_type, 1)
            score = weight * interaction.interaction_count
            
            data.append({
                'user_id': interaction.user_id,
                'provider_id': interaction.provider_id,
                'score': score
            })
        
        df = pd.DataFrame(data)
        
        # Pivot to create user-provider matrix
        self.user_provider_matrix = df.pivot_table(
            index='user_id',
            columns='provider_id',
            values='score',
            fill_value=0
        )
        
        return self.user_provider_matrix
    
    def build_provider_features(self, providers):
        """Build provider feature matrix for content-based filtering"""
        service_types = list(set([p.service_type for p in providers]))
        service_type_map = {st: i for i, st in enumerate(service_types)}
        
        features = []
        provider_ids = []
        
        for provider in providers:
            # One-hot encode service type
            service_vec = [0] * len(service_types)
            service_vec[service_type_map[provider.service_type]] = 1
            
            # Normalize numerical features
            feature_vec = service_vec + [
                provider.rating / 5.0,  # Normalize to 0-1
                min(provider.experience_years / 20.0, 1.0),  # Cap at 20 years
                provider.completion_rate,
                1.0 - min(provider.response_time / 24.0, 1.0),  # Lower is better
                1.0 if provider.verified else 0.0
            ]
            
            features.append(feature_vec)
            provider_ids.append(provider.id)
        
        self.provider_features = pd.DataFrame(features, index=provider_ids)
        
        # Calculate provider similarity matrix
        self.similarity_matrix = cosine_similarity(self.provider_features)
        
        return self.provider_features
    
    def collaborative_filtering(self, user_id, n_recommendations=10):
        """Recommend providers based on similar users' preferences"""
        if self.user_provider_matrix is None:
            return []
        
        if user_id not in self.user_provider_matrix.index:
            return []
        
        # Calculate user similarity
        user_similarity = cosine_similarity(self.user_provider_matrix)
        user_similarity_df = pd.DataFrame(
            user_similarity,
            index=self.user_provider_matrix.index,
            columns=self.user_provider_matrix.index
        )
        
        # Get similar users
        similar_users = user_similarity_df[user_id].sort_values(ascending=False)[1:6]
        
        # Get providers liked by similar users
        recommendations = {}
        for similar_user_id, similarity_score in similar_users.items():
            user_interactions = self.user_provider_matrix.loc[similar_user_id]
            for provider_id, score in user_interactions.items():
                if score > 0:
                    if provider_id not in recommendations:
                        recommendations[provider_id] = 0
                    recommendations[provider_id] += score * similarity_score
        
        # Sort and return top N
        sorted_recs = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
        return [provider_id for provider_id, _ in sorted_recs[:n_recommendations]]
    
    def content_based_filtering(self, provider_id, n_recommendations=10):
        """Recommend similar providers based on features"""
        if self.similarity_matrix is None or provider_id not in self.provider_features.index:
            return []
        
        provider_idx = self.provider_features.index.get_loc(provider_id)
        similarities = self.similarity_matrix[provider_idx]
        
        # Get most similar providers
        similar_indices = np.argsort(similarities)[::-1][1:n_recommendations+1]
        similar_provider_ids = [self.provider_features.index[i] for i in similar_indices]
        
        return similar_provider_ids
    
    def hybrid_recommend(self, user_id, providers, user_location=None, 
                        service_type=None, n_recommendations=5):
        """
        Hybrid recommendation combining collaborative, content-based, 
        and location-based filtering
        """
        scores = {}
        
        # Collaborative filtering (40% weight)
        collab_recs = self.collaborative_filtering(user_id, n_recommendations * 3)
        for i, provider_id in enumerate(collab_recs):
            scores[provider_id] = scores.get(provider_id, 0) + (0.4 * (len(collab_recs) - i))
        
        # Content-based filtering (30% weight)
        # Find providers user has interacted with
        if (self.user_provider_matrix is not None and 
            user_id in self.user_provider_matrix.index):
            user_history = self.user_provider_matrix.loc[user_id]
            top_providers = user_history.nlargest(3).index.tolist()
            
            for provider_id in top_providers:
                similar_providers = self.content_based_filtering(provider_id, n_recommendations * 2)
                for i, similar_id in enumerate(similar_providers):
                    scores[similar_id] = scores.get(similar_id, 0) + (0.3 * (len(similar_providers) - i))
        
        # Rating-based scoring (20% weight)
        for provider in providers:
            if service_type and provider.service_type != service_type:
                continue
            scores[provider.id] = scores.get(provider.id, 0) + (0.2 * provider.rating * 20)
        
        # Location-based scoring (10% weight)
        if user_location:
            user_lat, user_lon = user_location
            for provider in providers:
                if provider.latitude and provider.longitude:
                    distance = self.calculate_distance(
                        user_lat, user_lon,
                        provider.latitude, provider.longitude
                    )
                    # Closer is better (inverse distance, max 10km)
                    location_score = max(0, 10 - distance) / 10
                    scores[provider.id] = scores.get(provider.id, 0) + (0.1 * location_score * 100)
        
        # Sort by score
        sorted_providers = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        recommended_ids = [provider_id for provider_id, _ in sorted_providers[:n_recommendations]]
        
        # Return provider objects
        provider_dict = {p.id: p for p in providers}
        return [provider_dict[pid] for pid in recommended_ids if pid in provider_dict]
    
    def save_model(self, directory='models'):
        """Save recommendation model"""
        os.makedirs(directory, exist_ok=True)
        
        model_data = {
            'user_provider_matrix': self.user_provider_matrix,
            'provider_features': self.provider_features,
            'similarity_matrix': self.similarity_matrix
        }
        
        joblib.dump(model_data, os.path.join(directory, 'recommender.pkl'))
        print(f"✓ Recommender model saved to {directory}/recommender.pkl")
    
    def load_model(self, directory='models'):
        """Load recommendation model"""
        model_data = joblib.load(os.path.join(directory, 'recommender.pkl'))
        
        self.user_provider_matrix = model_data['user_provider_matrix']
        self.provider_features = model_data['provider_features']
        self.similarity_matrix = model_data['similarity_matrix']
        
        print(f"✓ Recommender model loaded from {directory}/recommender.pkl")


def train_recommender(interactions, providers):
    """Train and save recommender system"""
    print("Building recommendation system...")
    
    recommender = HybridRecommender()
    
    print("Building user-provider interaction matrix...")
    recommender.build_user_provider_matrix(interactions)
    print(f"Matrix shape: {recommender.user_provider_matrix.shape}")
    
    print("Building provider feature matrix...")
    recommender.build_provider_features(providers)
    print(f"Feature matrix shape: {recommender.provider_features.shape}")
    
    recommender.save_model()
    
    return recommender
