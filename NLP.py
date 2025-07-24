import re
import difflib
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from crop_pred import CropPredictor
from rain_pred import RainPredictor

class AgricultureNLP:
    def __init__(self):
        self.keywords = {
            'crop': ['crop', 'crops', 'cultivation', 'harvest', 'plant', 'growing', 'grown', 'grow', 'agriculture'],
            'rain': ['rain', 'rainfall', 'precipitation', 'monsoon', 'drought']
        }

        self.casual_responses = {
            'greetings': ['hi', 'hello', 'hey', 'greetings'],
            'how_are_you': ['how are you', 'how do you do'],
            'about_bot': ['who are you', 'what are you', 'what do you do'],
            'thanks': ['thank you', 'thanks', 'appreciate it'],
            'where are you from':['where are you from', 'where are you','where do you live']
        }

        crop_regions = CropPredictor().data['region'].str.lower().str.strip().unique()
        rain_regions = RainPredictor().data['Region'].str.lower().str.strip().unique()
        self.indian_states = sorted(set(crop_regions).union(set(rain_regions)))

    def preprocess_text(self, text):
        text = re.sub(r'[^\w\s]', '', text.lower())
        return [word for word in word_tokenize(text) if word not in stopwords.words('english')]

    def extract_keywords(self, text):
        result = {'intent': None, 'location': None, 'keywords': [], 'casual_intent': None, 'date': None}

        lowered = text.lower().replace('which ', 'what ')
        tokens = self.preprocess_text(lowered)

        # Handle casual conversation
        for intent, phrases in self.casual_responses.items():
            if any(phrase in lowered for phrase in phrases):
                result['casual_intent'] = intent
                return result

        # NEW: Weather forecast pattern match
        forecast_match = re.search(r'will it rain in ([\w\s]+)(?: (today|tomorrow|on \w+))?', lowered)
        if forecast_match:
            result['intent'] = 'weather_forecast'
            location = forecast_match.group(1).strip()
            result['location'] = location.title()
            date_phrase = forecast_match.group(2)
            if date_phrase:
                result['date'] = date_phrase.strip()
            else:
                result['date'] = 'tomorrow'
            return result

        # Region detection
        found_region = next((r for r in self.indian_states if r in lowered), None)
        if not found_region:
            matches = difflib.get_close_matches(lowered, self.indian_states, n=1, cutoff=0.6)
            found_region = matches[0] if matches else None
        result['location'] = found_region.title() if found_region else None

        # Keyword-based intent detection
        for intent_type, keywords in self.keywords.items():
            if any(word in lowered for word in keywords):
                result['intent'] = intent_type
                result['keywords'] = [kw for kw in keywords if kw in lowered]
                break

        if any(f in lowered for f in ['future', 'tomorrow', 'next week', 'next month']):
            result['keywords'].append('future')

        return result
