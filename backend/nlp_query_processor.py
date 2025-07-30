import re
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import Counter
import logging

# Robust imports with fallbacks
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("⚠️ spaCy not available. Install with: pip install spacy && python -m spacy download en_core_web_sm")

try:
    import nltk
    # Download required NLTK data with error handling
    try:
        nltk.download('punkt', quiet=True)
        nltk.download('punkt_tab', quiet=True)  # New requirement
        nltk.download('stopwords', quiet=True)
        nltk.download('wordnet', quiet=True)
        nltk.download('averaged_perceptron_tagger', quiet=True)
        nltk.download('vader_lexicon', quiet=True)
        NLTK_AVAILABLE = True
    except Exception as e:
        print(f"⚠️ NLTK download failed: {e}")
        NLTK_AVAILABLE = False
except ImportError:
    NLTK_AVAILABLE = False
    print("⚠️ NLTK not available. Install with: pip install nltk")

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    print("⚠️ TextBlob not available. Install with: pip install textblob")

# Import NLTK components with fallbacks
if NLTK_AVAILABLE:
    try:
        from nltk.corpus import stopwords
        from nltk.tokenize import word_tokenize
        from nltk.stem import WordNetLemmatizer
        from nltk.sentiment.vader import SentimentIntensityAnalyzer
    except Exception as e:
        print(f"⚠️ NLTK components failed to import: {e}")
        NLTK_AVAILABLE = False

@dataclass
class QueryIntent:
    """Structured representation of query intent"""
    primary_intent: str
    confidence: float
    secondary_intents: List[str]
    entities: Dict[str, List[str]]
    temporal_info: Dict[str, Any]
    complexity_level: str
    requires_visualization: bool
    data_operations: List[str]

@dataclass
class ProcessedQuery:
    """Complete processed query information"""
    original_query: str
    cleaned_query: str
    tokens: List[str]
    named_entities: Dict[str, List[str]]
    intent: QueryIntent
    column_references: List[str]
    temporal_expressions: Dict[str, Any]
    sentiment: Dict[str, float]
    urgency_level: str

class EnhancedNLPQueryProcessor:
    """
    Advanced NLP processor for understanding data analysis queries with robust fallbacks
    """
    
    def __init__(self, dataframe: pd.DataFrame = None):
        """Initialize the NLP processor with optional DataFrame context"""
        self.df = dataframe
        self.available_components = {
            'spacy': SPACY_AVAILABLE,
            'nltk': NLTK_AVAILABLE,
            'textblob': TEXTBLOB_AVAILABLE
        }
        self.setup_nlp_components()
        self.setup_intent_patterns()
        self.setup_entity_extractors()
        
    def setup_nlp_components(self):
        """Initialize all NLP components with fallbacks"""
        # spaCy setup
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                print("✅ spaCy model loaded successfully")
            except OSError:
                print("⚠️ spaCy model not found. Install with: python -m spacy download en_core_web_sm")
                self.nlp = None
                self.available_components['spacy'] = False
        else:
            self.nlp = None
            
        # NLTK setup
        if NLTK_AVAILABLE:
            try:
                self.lemmatizer = WordNetLemmatizer()
                self.sentiment_analyzer = SentimentIntensityAnalyzer()
                self.stop_words = set(stopwords.words('english'))
                print("✅ NLTK components loaded successfully")
            except Exception as e:
                print(f"⚠️ NLTK components failed: {e}")
                self.lemmatizer = None
                self.sentiment_analyzer = None
                self.stop_words = set()
                self.available_components['nltk'] = False
        else:
            self.lemmatizer = None
            self.sentiment_analyzer = None
            self.stop_words = set()
        
        # Fallback stop words
        if not self.stop_words:
            self.stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
                'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
                'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
                'this', 'that', 'these', 'those', 'what', 'where', 'when', 'why', 'how'
            }
        
        # Custom stop words for data analysis
        self.custom_stop_words = {
            'data', 'dataset', 'table', 'file', 'csv', 'column', 'row', 
            'please', 'could', 'would', 'can', 'show', 'tell', 'give'
        }
        self.stop_words.update(self.custom_stop_words)
        
    def setup_intent_patterns(self):
        """Define intent classification patterns"""
        self.intent_patterns = {
            'forecasting': {
                'keywords': [
                    'forecast', 'predict', 'prediction', 'future', 'next', 'coming',
                    'ahead', 'project', 'projection', 'estimate', 'anticipate',
                    'trend', 'outlook', 'expected', 'will be', 'gonna be'
                ],
                'patterns': [
                    r'forecast\s+(?:the\s+)?(?:next\s+)?(\d+)\s*(months?|years?|quarters?)',
                    r'predict\s+(?:the\s+)?(?:next\s+)?(\d+)',
                    r'what\s+will\s+(?:happen|be)',
                    r'(?:next|future|coming)\s+(\d+)',
                    r'project\s+(?:for\s+)?(?:the\s+)?(?:next\s+)?(\d+)'
                ],
                'confidence_boost': 0.3
            },
            'trend_analysis': {
                'keywords': [
                    'trend', 'trending', 'pattern', 'growth', 'decline', 'increase',
                    'decrease', 'rising', 'falling', 'change', 'evolution',
                    'progression', 'development', 'movement', 'direction'
                ],
                'patterns': [
                    r'(?:trend|pattern|growth)\s+(?:in|of|for)',
                    r'(?:increasing|decreasing|rising|falling)',
                    r'(?:over\s+time|through\s+time)',
                    r'(?:how\s+has|how\s+did).*(?:change|evolve)'
                ],
                'confidence_boost': 0.2
            },
            'comparison': {
                'keywords': [
                    'compare', 'comparison', 'versus', 'vs', 'against', 'between',
                    'difference', 'differ', 'contrast', 'relative', 'better',
                    'worse', 'higher', 'lower', 'top', 'bottom', 'best', 'worst'
                ],
                'patterns': [
                    r'compare\s+\w+\s+(?:to|with|against)',
                    r'\w+\s+vs\s+\w+',
                    r'difference\s+between',
                    r'(?:which|what)\s+(?:is\s+)?(?:better|worse|higher|lower)',
                    r'(?:top|best|worst|bottom)\s+\d+'
                ],
                'confidence_boost': 0.25
            },
            'aggregation': {
                'keywords': [
                    'total', 'sum', 'average', 'mean', 'median', 'count', 'number',
                    'maximum', 'minimum', 'max', 'min', 'aggregate', 'overall',
                    'combined', 'cumulative', 'distribution'
                ],
                'patterns': [
                    r'(?:total|sum|average|mean|count)\s+(?:of|for)',
                    r'(?:how\s+many|number\s+of)',
                    r'(?:maximum|minimum|max|min)\s+\w+',
                    r'overall\s+\w+'
                ],
                'confidence_boost': 0.2
            },
            'filtering': {
                'keywords': [
                    'filter', 'where', 'only', 'exclude', 'include', 'specific',
                    'particular', 'certain', 'subset', 'select', 'choose'
                ],
                'patterns': [
                    r'where\s+\w+\s+(?:is|equals?|=|>|<)',
                    r'only\s+(?:show|include|get)',
                    r'filter\s+(?:by|for|on)',
                    r'exclude\s+\w+'
                ],
                'confidence_boost': 0.2
            },
            'correlation': {
                'keywords': [
                    'correlation', 'correlate', 'relationship', 'related', 'connection',
                    'associated', 'influence', 'affect', 'impact', 'depend',
                    'linked', 'connected'
                ],
                'patterns': [
                    r'correlation\s+between',
                    r'relationship\s+between',
                    r'(?:how\s+)?(?:does|do)\s+\w+\s+(?:affect|influence|impact)',
                    r'(?:is|are)\s+\w+\s+related\s+to'
                ],
                'confidence_boost': 0.3
            },
            'visualization': {
                'keywords': [
                    'plot', 'chart', 'graph', 'visualize', 'show', 'display',
                    'draw', 'create', 'generate', 'bar', 'line', 'pie',
                    'scatter', 'histogram', 'heatmap'
                ],
                'patterns': [
                    r'(?:plot|chart|graph|visualize)\s+\w+',
                    r'(?:show|display)\s+(?:a\s+)?(?:chart|graph|plot)',
                    r'(?:bar|line|pie|scatter)\s+(?:chart|graph|plot)',
                    r'create\s+(?:a\s+)?(?:visualization|chart|graph)'
                ],
                'confidence_boost': 0.2
            },
            'reporting': {
                'keywords': [
                    'report', 'summary', 'overview', 'analysis', 'insights',
                    'findings', 'comprehensive', 'detailed', 'complete',
                    'full', 'strategic', 'executive'
                ],
                'patterns': [
                    r'(?:generate|create|write|make)\s+(?:a\s+)?report',
                    r'(?:comprehensive|detailed|full)\s+(?:analysis|report)',
                    r'(?:executive|strategic)\s+summary',
                    r'overview\s+of'
                ],
                'confidence_boost': 0.4
            },
            'data_quality': {
                'keywords': [
                    'missing', 'null', 'empty', 'clean', 'quality', 'duplicate',
                    'invalid', 'error', 'inconsistent', 'outlier', 'anomaly'
                ],
                'patterns': [
                    r'(?:missing|null|empty)\s+(?:values|data)',
                    r'(?:clean|quality)\s+(?:data|dataset)',
                    r'(?:duplicate|outlier)\s+\w+',
                    r'data\s+quality'
                ],
                'confidence_boost': 0.25
            }
        }
        
    def setup_entity_extractors(self):
        """Setup entity extraction patterns"""
        self.entity_patterns = {
            'temporal': {
                'relative_time': [
                    r'(?:last|past|previous)\s+(\d+)\s*(days?|weeks?|months?|years?)',
                    r'(?:next|coming|following)\s+(\d+)\s*(days?|weeks?|months?|years?)',
                    r'(\d+)\s*(?:days?|weeks?|months?|years?)\s+(?:ago|ahead)',
                ],
                'specific_periods': [
                    r'(january|february|march|april|may|june|july|august|september|october|november|december)',
                    r'(q1|q2|q3|q4|quarter\s+\d)',
                    r'(spring|summer|fall|autumn|winter)',
                    r'(\d{4})',  # Years
                ],
                'time_indicators': [
                    r'(?:daily|weekly|monthly|quarterly|yearly|annually)',
                    r'(?:today|tomorrow|yesterday)',
                    r'(?:this|that|current)\s+(?:week|month|quarter|year)',
                ]
            },
            'metrics': {
                'financial': [
                    'revenue', 'sales', 'profit', 'cost', 'expense', 'income',
                    'earnings', 'margin', 'roi', 'ebitda', 'cash flow'
                ],
                'performance': [
                    'growth', 'rate', 'percentage', 'ratio', 'kpi', 'metric',
                    'performance', 'efficiency', 'productivity'
                ],
                'statistical': [
                    'mean', 'average', 'median', 'mode', 'standard deviation',
                    'variance', 'correlation', 'regression', 'distribution'
                ]
            },
            'operations': {
                'mathematical': [
                    'sum', 'total', 'count', 'average', 'maximum', 'minimum',
                    'multiply', 'divide', 'subtract', 'add', 'calculate'
                ],
                'data_manipulation': [
                    'group', 'sort', 'filter', 'join', 'merge', 'pivot',
                    'transpose', 'reshape', 'transform'
                ]
            }
        }
        
    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess the input text"""
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Handle contractions
        contractions = {
            "won't": "will not", "can't": "cannot", "n't": " not",
            "'re": " are", "'ve": " have", "'ll": " will",
            "'d": " would", "'m": " am"
        }
        for contraction, expansion in contractions.items():
            text = text.replace(contraction, expansion)
        
        # Remove special characters but keep important ones for data analysis
        text = re.sub(r'[^\w\s\-\.\,\:\;\?\!]', '', text)
        
        return text
    
    def extract_named_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities using spaCy with fallback"""
        entities = {
            'PERSON': [], 'ORG': [], 'GPE': [], 'DATE': [],
            'MONEY': [], 'PERCENT': [], 'CARDINAL': [], 'ORDINAL': []
        }
        
        if self.nlp and self.available_components['spacy']:
            try:
                doc = self.nlp(text)
                for ent in doc.ents:
                    if ent.label_ in entities:
                        entities[ent.label_].append(ent.text)
            except Exception as e:
                print(f"⚠️ spaCy entity extraction failed: {e}")
        
        # Fallback: Simple regex-based entity extraction
        if not any(entities.values()):
            # Extract numbers
            numbers = re.findall(r'\b\d+\b', text)
            entities['CARDINAL'] = numbers[:5]  # Limit to 5
            
            # Extract percentages
            percentages = re.findall(r'\d+\s*%', text)
            entities['PERCENT'] = percentages
            
            # Extract years
            years = re.findall(r'\b(19|20)\d{2}\b', text)
            entities['DATE'] = years
        
        return entities
    
    def extract_column_references(self, text: str) -> List[str]:
        """Extract potential column references from the query"""
        if self.df is None:
            return []
        
        column_refs = []
        columns = self.df.columns.tolist()
        
        # Direct column name matches
        for col in columns:
            # Exact match (case insensitive)
            if col.lower() in text.lower():
                column_refs.append(col)
            
            # Partial match for multi-word columns
            col_words = col.lower().split('_')
            if len(col_words) > 1:
                if all(word in text.lower() for word in col_words):
                    column_refs.append(col)
        
        # Common column name patterns
        column_patterns = {
            r'(?:sales?|revenue|income)': ['sales', 'revenue', 'income'],
            r'(?:date|time|timestamp)': ['date', 'time', 'timestamp'],
            r'(?:price|cost|amount)': ['price', 'cost', 'amount'],
            r'(?:quantity|qty|volume)': ['quantity', 'qty', 'volume'],
            r'(?:customer|client|user)': ['customer', 'client', 'user'],
            r'(?:product|item|sku)': ['product', 'item', 'sku'],
            r'(?:category|type|class)': ['category', 'type', 'class']
        }
        
        for pattern, candidates in column_patterns.items():
            if re.search(pattern, text.lower()):
                for col in columns:
                    if any(candidate in col.lower() for candidate in candidates):
                        if col not in column_refs:
                            column_refs.append(col)
        
        return column_refs
    
    def extract_temporal_information(self, text: str) -> Dict[str, Any]:
        """Extract temporal information from the query"""
        temporal_info = {
            'has_temporal': False,
            'relative_periods': [],
            'specific_dates': [],
            'time_range': None,
            'forecast_periods': None,
            'frequency': None
        }
        
        # Extract relative time periods
        for pattern in self.entity_patterns['temporal']['relative_time']:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                temporal_info['has_temporal'] = True
                temporal_info['relative_periods'].append({
                    'quantity': int(match.group(1)),
                    'unit': match.group(2),
                    'text': match.group(0)
                })
        
        # Extract forecast periods
        forecast_patterns = [
            r'(?:forecast|predict).*?(\d+)\s*(months?|years?|quarters?|days?)',
            r'(?:next|coming)\s+(\d+)\s*(months?|years?|quarters?|days?)',
            r'for\s+(?:the\s+)?(?:next\s+)?(\d+)\s*(months?|years?|quarters?|days?)'
        ]
        
        for pattern in forecast_patterns:
            match = re.search(pattern, text.lower())
            if match:
                temporal_info['forecast_periods'] = {
                    'quantity': int(match.group(1)),
                    'unit': match.group(2)
                }
                break
        
        # Extract frequency indicators
        frequency_patterns = {
            'daily': r'(?:daily|every\s+day|day\s+by\s+day)',
            'weekly': r'(?:weekly|every\s+week|week\s+by\s+week)',
            'monthly': r'(?:monthly|every\s+month|month\s+by\s+month)',
            'quarterly': r'(?:quarterly|every\s+quarter|quarter\s+by\s+quarter)',
            'yearly': r'(?:yearly|annually|every\s+year|year\s+by\s+year)'
        }
        
        for freq, pattern in frequency_patterns.items():
            if re.search(pattern, text.lower()):
                temporal_info['frequency'] = freq
                break
        
        return temporal_info
    
    def classify_intent(self, text: str) -> QueryIntent:
        """Classify the primary intent of the query"""
        intent_scores = {}
        
        # Calculate scores for each intent
        for intent_name, intent_data in self.intent_patterns.items():
            score = 0
            
            # Keyword matching
            keywords_found = 0
            for keyword in intent_data['keywords']:
                if keyword in text.lower():
                    keywords_found += 1
                    score += 1
            
            # Pattern matching
            patterns_matched = 0
            for pattern in intent_data['patterns']:
                if re.search(pattern, text.lower()):
                    patterns_matched += 1
                    score += intent_data['confidence_boost']
            
            # Normalize score
            if keywords_found > 0 or patterns_matched > 0:
                intent_scores[intent_name] = score / len(intent_data['keywords'])
        
        # Determine primary intent
        if not intent_scores:
            primary_intent = 'general_analysis'
            confidence = 0.1
        else:
            primary_intent = max(intent_scores.keys(), key=lambda x: intent_scores[x])
            confidence = min(intent_scores[primary_intent], 1.0)
        
        # Determine secondary intents
        secondary_intents = [
            intent for intent, score in intent_scores.items() 
            if intent != primary_intent and score >= 0.3
        ]
        
        # Extract entities related to the intent
        entities = self.extract_intent_entities(text, primary_intent)
        
        # Determine complexity level
        complexity_level = self.determine_complexity(text, intent_scores)
        
        # Check if visualization is required
        requires_visualization = self.requires_visualization(text, primary_intent)
        
        # Extract data operations
        data_operations = self.extract_data_operations(text)
        
        # Extract temporal information
        temporal_info = self.extract_temporal_information(text)
        
        return QueryIntent(
            primary_intent=primary_intent,
            confidence=confidence,
            secondary_intents=secondary_intents,
            entities=entities,
            temporal_info=temporal_info,
            complexity_level=complexity_level,
            requires_visualization=requires_visualization,
            data_operations=data_operations
        )
    
    def extract_intent_entities(self, text: str, intent: str) -> Dict[str, List[str]]:
        """Extract entities specific to the detected intent"""
        entities = {'metrics': [], 'dimensions': [], 'operations': []}
        
        # Extract metrics based on intent
        if intent in ['forecasting', 'trend_analysis', 'correlation']:
            for metric_type, metrics in self.entity_patterns['metrics'].items():
                for metric in metrics:
                    if metric in text.lower():
                        entities['metrics'].append(metric)
        
        # Extract operations
        for op_type, operations in self.entity_patterns['operations'].items():
            for operation in operations:
                if operation in text.lower():
                    entities['operations'].append(operation)
        
        return entities
    
    def determine_complexity(self, text: str, intent_scores: Dict[str, float]) -> str:
        """Determine the complexity level of the query"""
        complexity_indicators = {
            'simple': ['show', 'display', 'what', 'total', 'count'],
            'medium': ['compare', 'analyze', 'trend', 'correlation', 'group'],
            'complex': ['forecast', 'predict', 'comprehensive', 'detailed', 'strategic', 'multiple']
        }
        
        scores = {'simple': 0, 'medium': 0, 'complex': 0}
        
        for level, indicators in complexity_indicators.items():
            for indicator in indicators:
                if indicator in text.lower():
                    scores[level] += 1
        
        # Consider multiple intents as complexity indicator
        if len(intent_scores) > 2:
            scores['complex'] += 2
        elif len(intent_scores) > 1:
            scores['medium'] += 1
        
        # Consider query length
        word_count = len(text.split())
        if word_count > 20:
            scores['complex'] += 1
        elif word_count > 10:
            scores['medium'] += 1
        
        return max(scores.keys(), key=lambda x: scores[x])
    
    def requires_visualization(self, text: str, intent: str) -> bool:
        """Determine if the query requires visualization"""
        viz_keywords = [
            'plot', 'chart', 'graph', 'visualize', 'show', 'display',
            'trend', 'pattern', 'comparison', 'distribution'
        ]
        
        # Direct visualization requests
        if any(keyword in text.lower() for keyword in viz_keywords):
            return True
        
        # Intent-based visualization requirements
        visualization_intents = ['trend_analysis', 'comparison', 'forecasting', 'correlation']
        if intent in visualization_intents:
            return True
        
        return False
    
    def extract_data_operations(self, text: str) -> List[str]:
        """Extract specific data operations requested"""
        operations = []
        
        operation_patterns = {
            'group_by': r'group\s+by\s+\w+',
            'sort': r'sort\s+by\s+\w+',
            'filter': r'(?:filter|where)\s+\w+',
            'aggregate': r'(?:sum|count|average|total)\s+\w+',
            'join': r'(?:join|merge)\s+\w+',
            'pivot': r'pivot\s+\w+',
            'calculate': r'calculate\s+\w+',
            'rank': r'(?:rank|top|bottom)\s+\w+'
        }
        
        for operation, pattern in operation_patterns.items():
            if re.search(pattern, text.lower()):
                operations.append(operation)
        
        return operations
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of the query with fallback"""
        if self.sentiment_analyzer and self.available_components['nltk']:
            try:
                sentiment_scores = self.sentiment_analyzer.polarity_scores(text)
            except Exception as e:
                print(f"⚠️ NLTK sentiment analysis failed: {e}")
                sentiment_scores = {'compound': 0.0, 'pos': 0.0, 'neg': 0.0, 'neu': 1.0}
        elif TEXTBLOB_AVAILABLE:
            try:
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity
                sentiment_scores = {
                    'compound': polarity,
                    'pos': max(0, polarity),
                    'neg': max(0, -polarity),
                    'neu': 1 - abs(polarity)
                }
            except Exception as e:
                print(f"⚠️ TextBlob sentiment analysis failed: {e}")
                sentiment_scores = {'compound': 0.0, 'pos': 0.0, 'neg': 0.0, 'neu': 1.0}
        else:
            # Simple fallback sentiment analysis
            positive_words = ['good', 'great', 'excellent', 'best', 'high', 'increase']
            negative_words = ['bad', 'poor', 'worst', 'low', 'decrease', 'decline']
            
            pos_count = sum(1 for word in positive_words if word in text.lower())
            neg_count = sum(1 for word in negative_words if word in text.lower())
            
            if pos_count > neg_count:
                sentiment_scores = {'compound': 0.5, 'pos': 0.7, 'neg': 0.1, 'neu': 0.2}
            elif neg_count > pos_count:
                sentiment_scores = {'compound': -0.5, 'pos': 0.1, 'neg': 0.7, 'neu': 0.2}
            else:
                sentiment_scores = {'compound': 0.0, 'pos': 0.0, 'neg': 0.0, 'neu': 1.0}
        
        # Determine urgency based on sentiment and specific words
        urgency_keywords = ['urgent', 'asap', 'immediately', 'quickly', 'fast', 'now']
        urgency_score = sum(1 for word in urgency_keywords if word in text.lower())
        sentiment_scores['urgency_score'] = urgency_score
        
        return sentiment_scores
    
    def determine_urgency(self, sentiment: Dict[str, float], text: str) -> str:
        """Determine urgency level of the query"""
        urgency_indicators = {
            'high': ['urgent', 'asap', 'immediately', 'critical', 'emergency'],
            'medium': ['soon', 'quickly', 'fast', 'priority'],
            'low': ['when possible', 'eventually', 'sometime']
        }
        
        # Check for explicit urgency indicators
        for level, indicators in urgency_indicators.items():
            if any(indicator in text.lower() for indicator in indicators):
                return level
        
        # Use sentiment urgency score
        urgency_score = sentiment.get('urgency_score', 0)
        if urgency_score >= 2:
            return 'high'
        elif urgency_score >= 1:
            return 'medium'
        else:
            return 'low'
    
    def tokenize_and_lemmatize(self, text: str) -> List[str]:
        """Tokenize and lemmatize the text with fallbacks"""
        processed_tokens = []
        
        if NLTK_AVAILABLE and self.available_components['nltk']:
            try:
                from nltk.tokenize import word_tokenize
                tokens = word_tokenize(text.lower())
                
                # Remove stopwords and lemmatize
                for token in tokens:
                    if token not in self.stop_words and token.isalpha() and len(token) > 2:
                        if self.lemmatizer:
                            lemmatized = self.lemmatizer.lemmatize(token)
                            processed_tokens.append(lemmatized)
                        else:
                            processed_tokens.append(token)
                            
            except Exception as e:
                print(f"⚠️ NLTK tokenization failed: {e}")
                # Fallback to simple tokenization
                processed_tokens = self._simple_tokenize(text)
        else:
            # Simple fallback tokenization
            processed_tokens = self._simple_tokenize(text)
        
        return processed_tokens
    
    def _simple_tokenize(self, text: str) -> List[str]:
        """Simple fallback tokenization"""
        # Simple word splitting and filtering
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter out stop words
        filtered_words = [word for word in words if word not in self.stop_words]
        
        return filtered_words
    
    def process_query(self, query: str) -> ProcessedQuery:
        """Main method to process a complete query with robust error handling"""
        try:
            # Preprocess text
            cleaned_query = self.preprocess_text(query)
            
            # Tokenize and lemmatize
            tokens = self.tokenize_and_lemmatize(cleaned_query)
            
            # Extract named entities
            named_entities = self.extract_named_entities(cleaned_query)
            
            # Classify intent
            intent = self.classify_intent(cleaned_query)
            
            # Extract column references
            column_references = self.extract_column_references(cleaned_query)
            
            # Extract temporal expressions
            temporal_expressions = self.extract_temporal_information(cleaned_query)
            
            # Analyze sentiment
            sentiment = self.analyze_sentiment(cleaned_query)
            
            # Determine urgency
            urgency_level = self.determine_urgency(sentiment, cleaned_query)
            
            return ProcessedQuery(
                original_query=query,
                cleaned_query=cleaned_query,
                tokens=tokens,
                named_entities=named_entities,
                intent=intent,
                column_references=column_references,
                temporal_expressions=temporal_expressions,
                sentiment=sentiment,
                urgency_level=urgency_level
            )
            
        except Exception as e:
            print(f"⚠️ Query processing failed: {e}")
            # Return minimal processed query
            return self._create_fallback_processed_query(query)
    
    def _create_fallback_processed_query(self, query: str) -> ProcessedQuery:
        """Create a minimal processed query when full processing fails"""
        # Simple intent detection based on keywords
        intent_keywords = {
            'forecasting': ['forecast', 'predict', 'future'],
            'trend_analysis': ['trend', 'growth', 'change'],
            'comparison': ['compare', 'vs', 'versus'],
            'aggregation': ['total', 'sum', 'average'],
            'reporting': ['report', 'summary', 'analysis']
        }
        
        detected_intent = 'general_analysis'
        for intent, keywords in intent_keywords.items():
            if any(keyword in query.lower() for keyword in keywords):
                detected_intent = intent
                break
        
        # Create minimal intent object
        minimal_intent = QueryIntent(
            primary_intent=detected_intent,
            confidence=0.5,
            secondary_intents=[],
            entities={},
            temporal_info={},
            complexity_level='medium',
            requires_visualization=any(word in query.lower() for word in ['chart', 'plot', 'graph', 'visualize']),
            data_operations=[]
        )
        
        # Simple tokenization
        simple_tokens = re.findall(r'\b[a-zA-Z]{3,}\b', query.lower())
        
        return ProcessedQuery(
            original_query=query,
            cleaned_query=query.lower(),
            tokens=simple_tokens[:10],  # Limit tokens
            named_entities={'CARDINAL': [], 'DATE': [], 'PERCENT': []},
            intent=minimal_intent,
            column_references=self.extract_column_references(query) if self.df is not None else [],
            temporal_expressions={'has_temporal': any(word in query.lower() for word in ['month', 'year', 'day', 'forecast'])},
            sentiment={'compound': 0.0, 'pos': 0.0, 'neg': 0.0, 'neu': 1.0, 'urgency_score': 0},
            urgency_level='medium'
        )
    
    def generate_enhanced_prompt(self, processed_query: ProcessedQuery) -> str:
        """Generate an enhanced prompt based on processed query"""
        base_prompt = f"Original Query: {processed_query.original_query}\n\n"
        
        # Add intent information
        base_prompt += f"DETECTED INTENT: {processed_query.intent.primary_intent.upper()}\n"
        base_prompt += f"Confidence: {processed_query.intent.confidence:.2f}\n"
        
        if processed_query.intent.secondary_intents:
            base_prompt += f"Secondary Intents: {', '.join(processed_query.intent.secondary_intents)}\n"
        
        # Add complexity and urgency
        base_prompt += f"Complexity Level: {processed_query.intent.complexity_level}\n"
        base_prompt += f"Urgency: {processed_query.urgency_level}\n\n"
        
        # Add column references
        if processed_query.column_references:
            base_prompt += f"RELEVANT COLUMNS: {', '.join(processed_query.column_references)}\n\n"
        
        # Add temporal information
        if processed_query.temporal_expressions.get('has_temporal'):
            base_prompt += "TEMPORAL REQUIREMENTS:\n"
            if processed_query.temporal_expressions.get('forecast_periods'):
                fp = processed_query.temporal_expressions['forecast_periods']
                base_prompt += f"- Forecast: {fp['quantity']} {fp['unit']}\n"
            if processed_query.temporal_expressions.get('frequency'):
                base_prompt += f"- Frequency: {processed_query.temporal_expressions['frequency']}\n"
            base_prompt += "\n"
        
        # Add data operations
        if processed_query.intent.data_operations:
            base_prompt += f"DATA OPERATIONS: {', '.join(processed_query.intent.data_operations)}\n\n"
        
        # Add visualization requirements
        if processed_query.intent.requires_visualization:
            base_prompt += "VISUALIZATION REQUIRED: Yes\n\n"
        
        # Add specific instructions based on intent
        intent_instructions = self.get_intent_specific_instructions(processed_query.intent)
        if intent_instructions:
            base_prompt += f"SPECIFIC INSTRUCTIONS:\n{intent_instructions}\n\n"
        
        return base_prompt
    
    def get_intent_specific_instructions(self, intent: QueryIntent) -> str:
        """Get specific instructions based on detected intent"""
        instructions = {
            'forecasting': """
- Generate future predictions beyond the historical data range
- Use appropriate forecasting models (ARIMA, Linear Regression, etc.)
- Include confidence intervals
- Create separate forecast DataFrame with future dates
- Visualize historical vs predicted data with clear separation
""",
            'trend_analysis': """
- Analyze patterns over time
- Calculate trend direction and strength
- Identify seasonal patterns if applicable
- Create trend visualizations (line charts)
- Add trend indicators to the data
""",
            'comparison': """
- Compare specified entities/categories
- Use appropriate comparison metrics
- Create comparative visualizations (bar charts, grouped plots)
- Highlight significant differences
""",
            'aggregation': """
- Perform requested aggregation operations
- Group by relevant dimensions
- Create summary statistics
- Generate aggregate visualizations
""",
            'correlation': """
- Calculate correlation coefficients
- Identify strong relationships
- Create correlation matrices/heatmaps
- Analyze statistical significance
""",
            'reporting': """
- Generate comprehensive analysis report
- Include executive summary
- Add strategic insights and recommendations
- Create professional visualizations
- Structure as formal business report
"""
        }
        
        return instructions.get(intent.primary_intent, "")


# Example usage and integration helper
class QueryProcessorIntegration:
    """Helper class to integrate the NLP processor with existing systems"""
    
    def __init__(self, dataframe: pd.DataFrame = None):
        self.processor = EnhancedNLPQueryProcessor(dataframe)
    
    def update_dataframe(self, dataframe: pd.DataFrame):
        """Update the processor with new dataframe"""
        self.processor.df = dataframe
    
    def process_and_enhance_query(self, query: str) -> Tuple[ProcessedQuery, str]:
        """Process query and return enhanced prompt for AI"""
        processed_query = self.processor.process_query(query)
        enhanced_prompt = self.processor.generate_enhanced_prompt(processed_query)
        return processed_query, enhanced_prompt
    
    def get_query_insights(self, query: str) -> Dict[str, Any]:
        """Get comprehensive insights about the query"""
        processed_query = self.processor.process_query(query)
        
        return {
            'intent': {
                'primary': processed_query.intent.primary_intent,
                'confidence': processed_query.intent.confidence,
                'secondary': processed_query.intent.secondary_intents,
                'complexity': processed_query.intent.complexity_level
            },
            'entities': {
                'columns': processed_query.column_references,
                'temporal': processed_query.temporal_expressions,
                'named_entities': processed_query.named_entities,
                'operations': processed_query.intent.data_operations
            },
            'requirements': {
                'visualization': processed_query.intent.requires_visualization,
                'urgency': processed_query.urgency_level,
                'sentiment': processed_query.sentiment
            },
            'tokens': processed_query.tokens,
            'cleaned_query': processed_query.cleaned_query
        }


if __name__ == "__main__":
    # Example usage and testing
    print("🧠 NLP Query Processor Example (Robust Version)")
    print("=" * 60)
    
    # Sample DataFrame for testing
    sample_data = {
        'date': pd.date_range('2023-01-01', periods=100, freq='D'),
        'sales': np.random.randint(100, 1000, 100),
        'revenue': np.random.randint(1000, 10000, 100),
        'product_category': np.random.choice(['A', 'B', 'C'], 100),
        'customer_count': np.random.randint(10, 100, 100)
    }
    df = pd.DataFrame(sample_data)
    
    # Initialize processor
    processor = EnhancedNLPQueryProcessor(df)
    
    print(f"📊 Available NLP Components:")
    print(f"   - spaCy: {processor.available_components['spacy']}")
    print(f"   - NLTK: {processor.available_components['nltk']}")
    print(f"   - TextBlob: {processor.available_components['textblob']}")
    
    # Test queries
    test_queries = [
        "forecast sales for the next 12 months",
        "show me the trend in revenue over time",
        "compare product categories by performance", 
        "what's the correlation between sales and customer count?",
        "create a comprehensive report on business performance",
        "filter data where sales is greater than 500",
        "urgently show me top 10 sales days",
        "predict revenue trends for next quarter"
    ]
    
    print("\n📝 Testing Query Processing:")
    print("-" * 50)
    
    for query in test_queries:
        print(f"\n🔍 Query: \"{query}\"")
        print("-" * 35)
        
        try:
            processed = processor.process_query(query)
            print(f"✅ Intent: {processed.intent.primary_intent} (confidence: {processed.intent.confidence:.2f})")
            print(f"   Complexity: {processed.intent.complexity_level}")
            print(f"   Urgency: {processed.urgency_level}")
            print(f"   Columns: {processed.column_references}")
            print(f"   Temporal: {processed.temporal_expressions.get('has_temporal', False)}")
            print(f"   Visualization: {processed.intent.requires_visualization}")
            print(f"   Operations: {processed.intent.data_operations}")
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")
    
    print("\n" + "=" * 60)
    print("✅ NLP Query Processor testing complete!")
    print("\nTo use in your Flask app:")
    print("1. Save this file as 'nlp_query_processor.py'")
    print("2. Install optional dependencies:")
    print("   pip install spacy nltk textblob")
    print("   python -m spacy download en_core_web_sm")
    print("   python -c \"import nltk; nltk.download('punkt_tab')\"")
    print("3. The processor will work with fallbacks even if dependencies are missing!")
    print("4. Import and use in your Flask app as shown in the documentation")