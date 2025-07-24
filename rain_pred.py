import pandas as pd
from datetime import datetime
import calendar
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB

class RainPredictor:
    def __init__(self, data_path='rainfall_data.csv'):
        self.data = pd.read_csv(data_path)
        self._preprocess_data()

    def _preprocess_data(self):
        """Clean and prepare rainfall data with annual aggregation."""
        self.data['Month'] = self.data['Month'].str.strip().str.title()
        self.data['Month_Num'] = self.data['Month'].apply(lambda x: list(calendar.month_name).index(x))
        self.data['Date'] = pd.to_datetime(
            self.data['Year'].astype(str) + '-' +
            self.data['Month_Num'].astype(str) + '-01'
        )
        
        # Calculate annual rainfall per region per year
        annual_rainfall = self.data.groupby(['Region', 'Year'])['Rainfall (mm)'].sum().reset_index()
        annual_rainfall.rename(columns={'Rainfall (mm)': 'ANNUAL'}, inplace=True)
        self.data = pd.merge(self.data, annual_rainfall, on=['Region', 'Year'])

    def get_average_rainfall(self, region):
        """Return historical average rainfall for a region."""
        df = self.data[self.data['Region'].str.lower() == region.lower()]
        if df.empty:
            return None
        return {
            'region': region.title(),
            'average_rainfall': round(df['Rainfall (mm)'].mean(), 2),
            'unit': 'mm'
        }

    def predict_future_rainfall(self, region):
        """Predict next month’s rainfall using ensemble of models."""
        now = datetime.now()
        next_mon = now.month % 12 + 1
        name = calendar.month_name[next_mon]

        hist = self.data[
            (self.data['Region'].str.lower() == region.lower()) &
            (self.data['Month_Num'] == next_mon)
        ]
        if hist.empty:
            return None

        # Prepare features and target
        X = hist[['Year', 'ANNUAL']]
        y = hist['Rainfall (mm)']
        if len(y) < 3:  # Ensure minimum data points
            return None

        # Encode target variable
        lab_enc = LabelEncoder()
        y_encoded = lab_enc.fit_transform(y)
        
        # Train models on entire dataset (for simplicity)
        models = [
            DecisionTreeClassifier(),
            RandomForestClassifier(),
            SVC(kernel='rbf', random_state=1),
            LogisticRegression(max_iter=1000),
            GaussianNB()
        ]
        
        predictions = []
        current_year = datetime.now().year
        next_year = current_year + 1
        latest_annual = hist['ANNUAL'].iloc[-1]  # Use latest annual data

        for model in models:
            model.fit(X, y_encoded)
            pred_encoded = model.predict([[next_year, latest_annual]])
            predictions.append(pred_encoded[0])

        # Average and decode prediction
        avg_encoded = sum(predictions) / len(predictions)
        predicted_rainfall = lab_enc.inverse_transform([int(round(avg_encoded))])[0]

        return {
            'region': region.title(),
            'month': name,
            'predicted_rainfall': round(predicted_rainfall, 2),
            'unit': 'mm',
            'confidence': 'high' if len(hist) >= 5 else 'medium'
        }