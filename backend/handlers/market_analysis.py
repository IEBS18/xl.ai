# handlers/market_intelligence.py
import os
import logging
from pathlib import Path
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd

# Try importing GNews with fallback
try:
    from gnews import GNews
    PYNEWS_AVAILABLE = True
except ImportError:
    PYNEWS_AVAILABLE = False
    logging.warning("GNews not available. Install with: pip install gnews-api")

# For sentiment analysis fallback
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

class MarketIntelligenceProvider:
    """
    Provides real-time market intelligence and news data using GNews API.
    Integrates with CSV analysis to provide contextual market insights.
    """
    
    # def __init__(self, api_key: str = None):
    #     self.api_key = api_key or os.getenv('PYNEWS_API_KEY')
    #     self.pynews_client = None
        
    #     if PYNEWS_AVAILABLE and self.api_key:
    #         try:
    #             self.pynews_client = GNews(api_key=self.api_key)
    #             logging.info("✅ GNews client initialized successfully")
    #         except Exception as e:
    #             logging.error(f"❌ Failed to initialize GNews client: {e}")
    #     else:
    #         logging.warning("⚠️ GNews API key not found. Market intelligence will use fallback methods.")
    
    def fetch_market_news(self, query_keywords: List[str], region: str = "US", 
                         language: str = "en", limit: int = 10) -> Dict[str, Any]:
        """
        Fetch market news based on query keywords.
        
        Args:
            query_keywords: List of keywords extracted from user query and CSV data
            region: Geographic region for news filtering
            language: Language preference
            limit: Maximum number of articles to fetch
            
        Returns:
            Dictionary containing news articles and metadata
        """
        try:
            if not PYNEWS_AVAILABLE:
                return self._get_fallback_market_data(query_keywords)
            
            # Combine keywords into search query
            search_query = " OR ".join(query_keywords[:3])  # Limit to top 3 keywords
            
            # Fetch news using GNews
            news_data = GNews.get_news(
                query=search_query,
                country=region.lower(),
                language=language,
                page_size=limit,
                sort_by="relevancy"
            )
            
            # Process and format results
            processed_articles = []
            if news_data and 'articles' in news_data:
                for article in news_data['articles'][:limit]:
                    processed_article = {
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'url': article.get('url', ''),
                        'source': article.get('source', {}).get('name', 'Unknown'),
                        'published_at': article.get('publishedAt', ''),
                        'relevance_score': self._calculate_relevance_score(
                            article, query_keywords
                        ),
                        'sentiment': self._analyze_article_sentiment(article)
                    }
                    processed_articles.append(processed_article)
            
            # Sort by relevance score
            processed_articles.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            return {
                'success': True,
                'articles': processed_articles,
                'total_found': len(processed_articles),
                'query_keywords': query_keywords,
                'search_query': search_query,
                'timestamp': datetime.now().isoformat(),
                'source': 'gnews'
            }
            
        except Exception as e:
            logging.error(f"❌ Error fetching market news: {e}")
            return self._get_fallback_market_data(query_keywords)
    
    def analyze_market_sentiment(self, news_articles: List[Dict]) -> Dict[str, Any]:
        """
        Analyze sentiment of news articles.
        
        Args:
            news_articles: List of news articles
            
        Returns:
            Sentiment analysis summary
        """
        try:
            if not news_articles:
                return {'sentiment': 'neutral', 'confidence': 0.0, 'summary': 'No articles to analyze'}
            
            sentiments = []
            sentiment_scores = []
            
            for article in news_articles:
                article_sentiment = article.get('sentiment', {})
                if article_sentiment:
                    sentiments.append(article_sentiment.get('label', 'neutral'))
                    sentiment_scores.append(article_sentiment.get('score', 0.0))
            
            if not sentiments:
                return {'sentiment': 'neutral', 'confidence': 0.0, 'summary': 'Unable to analyze sentiment'}
            
            # Calculate overall sentiment
            positive_count = sentiments.count('positive')
            negative_count = sentiments.count('negative')
            neutral_count = sentiments.count('neutral')
            
            total_articles = len(sentiments)
            
            # Determine overall sentiment
            if positive_count > negative_count and positive_count > neutral_count:
                overall_sentiment = 'positive'
            elif negative_count > positive_count and negative_count > neutral_count:
                overall_sentiment = 'negative'
            else:
                overall_sentiment = 'neutral'
            
            # Calculate confidence based on sentiment distribution
            max_count = max(positive_count, negative_count, neutral_count)
            confidence = max_count / total_articles if total_articles > 0 else 0.0
            
            summary = f"Market sentiment is {overall_sentiment} based on {total_articles} articles. " \
                     f"{positive_count} positive, {negative_count} negative, {neutral_count} neutral."
            
            return {
                'sentiment': overall_sentiment,
                'confidence': confidence,
                'distribution': {
                    'positive': positive_count,
                    'negative': negative_count,
                    'neutral': neutral_count,
                    'total': total_articles
                },
                'summary': summary,
                'average_score': sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
            }
            
        except Exception as e:
            logging.error(f"❌ Error analyzing market sentiment: {e}")
            return {'sentiment': 'neutral', 'confidence': 0.0, 'summary': f'Sentiment analysis failed: {str(e)}'}
    
    def extract_market_trends(self, query: str, data_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract market trends from query and data context.
        
        Args:
            query: User query
            data_context: Context from CSV data analysis
            
        Returns:
            Market trends analysis
        """
        try:
            trends = {
                'identified_trends': [],
                'business_domain': self._identify_business_domain(query, data_context),
                'key_metrics': self._extract_key_metrics(data_context),
                'growth_indicators': self._analyze_growth_patterns(data_context),
                'market_position': self._assess_market_position(data_context),
                'risk_factors': self._identify_risk_factors(query, data_context)
            }
            
            # Extract trends from data patterns
            if 'dataframes' in data_context:
                for df_name, df_info in data_context['dataframes'].items():
                    if isinstance(df_info, dict) and 'data' in df_info:
                        df = df_info['data']
                        if isinstance(df, pd.DataFrame):
                            trend_analysis = self._analyze_dataframe_trends(df, df_name)
                            trends['identified_trends'].extend(trend_analysis)
            
            return trends
            
        except Exception as e:
            logging.error(f"❌ Error extracting market trends: {e}")
            return {
                'identified_trends': [],
                'business_domain': 'general',
                'error': str(e)
            }
    
    def get_industry_context(self, business_domain: str) -> Dict[str, Any]:
        """
        Get industry context for the identified business domain.
        
        Args:
            business_domain: Identified business domain
            
        Returns:
            Industry context and insights
        """
        industry_contexts = {
            'sales': {
                'key_metrics': ['revenue', 'conversion_rate', 'customer_acquisition_cost', 'churn_rate'],
                'market_factors': ['economic_conditions', 'competition', 'seasonal_trends'],
                'growth_drivers': ['new_markets', 'product_innovation', 'customer_retention'],
                'common_challenges': ['market_saturation', 'price_competition', 'customer_expectations']
            },
            'retail': {
                'key_metrics': ['sales_volume', 'profit_margin', 'inventory_turnover', 'customer_satisfaction'],
                'market_factors': ['consumer_behavior', 'supply_chain', 'digital_transformation'],
                'growth_drivers': ['omnichannel_strategy', 'personalization', 'sustainability'],
                'common_challenges': ['online_competition', 'supply_disruptions', 'changing_preferences']
            },
            'technology': {
                'key_metrics': ['user_growth', 'engagement_rate', 'revenue_per_user', 'development_velocity'],
                'market_factors': ['innovation_pace', 'regulatory_changes', 'talent_availability'],
                'growth_drivers': ['ai_integration', 'cloud_adoption', 'automation'],
                'common_challenges': ['cybersecurity', 'data_privacy', 'technical_debt']
            },
            'finance': {
                'key_metrics': ['roi', 'risk_metrics', 'liquidity_ratios', 'growth_rates'],
                'market_factors': ['interest_rates', 'regulations', 'market_volatility'],
                'growth_drivers': ['digital_banking', 'fintech_innovation', 'data_analytics'],
                'common_challenges': ['regulatory_compliance', 'cybersecurity', 'market_disruption']
            }
        }
        
        return industry_contexts.get(business_domain, industry_contexts['sales'])
    
    def format_news_for_report(self, news_data: Dict[str, Any]) -> str:
        """
        Format news data for HTML report integration.
        
        Args:
            news_data: News data from fetch_market_news
            
        Returns:
            HTML formatted news section
        """
        try:
            if not news_data.get('success') or not news_data.get('articles'):
                return self._get_fallback_market_section()
            
            articles = news_data['articles'][:5]  # Top 5 articles
            sentiment_data = self.analyze_market_sentiment(articles)
            
            html_content = f"""
            <div class="market-intelligence-section">
                <h3>📰 Market Intelligence & News</h3>
                
                <div class="sentiment-overview">
                    <p><strong>Overall Market Sentiment:</strong> 
                    <span class="sentiment-{sentiment_data['sentiment']}">{sentiment_data['sentiment'].title()}</span>
                    (Confidence: {sentiment_data['confidence']:.1%})</p>
                    <p><em>{sentiment_data['summary']}</em></p>
                </div>
                
                <div class="news-articles">
                    <h4>Recent Market Developments</h4>
            """
            
            for i, article in enumerate(articles, 1):
                published_date = self._format_date(article.get('published_at', ''))
                sentiment_icon = self._get_sentiment_icon(article.get('sentiment', {}).get('label', 'neutral'))
                
                html_content += f"""
                    <div class="news-article">
                        <div class="article-header">
                            <span class="article-number">{i}.</span>
                            <span class="sentiment-indicator">{sentiment_icon}</span>
                            <span class="article-source">{article.get('source', 'Unknown Source')}</span>
                            <span class="article-date">{published_date}</span>
                        </div>
                        <h5 class="article-title">{article.get('title', 'No Title')}</h5>
                        <p class="article-description">{article.get('description', 'No description available.')}</p>
                        <div class="article-metrics">
                            <span class="relevance-score">Relevance: {article.get('relevance_score', 0.0):.1f}/10</span>
                        </div>
                    </div>
                """
            
            html_content += """
                </div>
                
                <div class="market-insights">
                    <h4>Key Market Insights</h4>
                    <ul>
                        <li>Monitor industry trends affecting your data patterns</li>
                        <li>Consider external market factors in strategic planning</li>
                        <li>Stay informed about competitive landscape changes</li>
                    </ul>
                </div>
            </div>
            """
            
            return html_content
            
        except Exception as e:
            logging.error(f"❌ Error formatting news for report: {e}")
            return self._get_fallback_market_section()
    
    def _calculate_relevance_score(self, article: Dict, keywords: List[str]) -> float:
        """Calculate relevance score for an article based on keywords"""
        try:
            title = article.get('title', '').lower()
            description = article.get('description', '').lower()
            content = f"{title} {description}"
            
            score = 0.0
            for keyword in keywords:
                keyword_lower = keyword.lower()
                # Title matches get higher score
                if keyword_lower in title:
                    score += 3.0
                # Description matches get medium score
                elif keyword_lower in description:
                    score += 1.5
                # Partial matches get lower score
                elif any(word in content for word in keyword_lower.split()):
                    score += 0.5
            
            # Normalize score to 0-10 range
            max_possible_score = len(keywords) * 3.0
            normalized_score = min(10.0, (score / max_possible_score) * 10.0) if max_possible_score > 0 else 0.0
            
            return round(normalized_score, 1)
            
        except Exception as e:
            logging.error(f"Error calculating relevance score: {e}")
            return 0.0
    
    def _analyze_article_sentiment(self, article: Dict) -> Dict[str, Any]:
        """Analyze sentiment of individual article"""
        try:
            text = f"{article.get('title', '')} {article.get('description', '')}"
            
            if TEXTBLOB_AVAILABLE and text.strip():
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity
                
                if polarity > 0.1:
                    sentiment = 'positive'
                elif polarity < -0.1:
                    sentiment = 'negative'
                else:
                    sentiment = 'neutral'
                
                return {
                    'label': sentiment,
                    'score': abs(polarity),
                    'confidence': min(1.0, abs(polarity) * 2),  # Scale confidence
                    'raw_polarity': polarity
                }
            else:
                # Keyword-based fallback sentiment analysis
                positive_words = ['growth', 'increase', 'profit', 'success', 'up', 'gain', 'positive', 'strong']
                negative_words = ['decline', 'decrease', 'loss', 'down', 'fall', 'negative', 'weak', 'crisis']
                
                text_lower = text.lower()
                positive_count = sum(1 for word in positive_words if word in text_lower)
                negative_count = sum(1 for word in negative_words if word in text_lower)
                
                if positive_count > negative_count:
                    sentiment = 'positive'
                    score = positive_count / (positive_count + negative_count + 1)
                elif negative_count > positive_count:
                    sentiment = 'negative'
                    score = negative_count / (positive_count + negative_count + 1)
                else:
                    sentiment = 'neutral'
                    score = 0.5
                
                return {
                    'label': sentiment,
                    'score': score,
                    'confidence': score,
                    'method': 'keyword_based'
                }
                
        except Exception as e:
            logging.error(f"Error analyzing article sentiment: {e}")
            return {'label': 'neutral', 'score': 0.0, 'confidence': 0.0, 'error': str(e)}
    
    def _identify_business_domain(self, query: str, data_context: Dict[str, Any]) -> str:
        """Identify business domain from query and data"""
        try:
            query_lower = query.lower()
            
            # Check query for domain indicators
            domain_keywords = {
                'sales': ['sales', 'revenue', 'selling', 'customers', 'conversion'],
                'retail': ['retail', 'store', 'products', 'inventory', 'merchandise'],
                'technology': ['tech', 'software', 'users', 'platform', 'digital'],
                'finance': ['finance', 'financial', 'money', 'investment', 'profit', 'cost'],
                'marketing': ['marketing', 'campaign', 'leads', 'engagement', 'acquisition'],
                'operations': ['operations', 'process', 'efficiency', 'logistics', 'supply']
            }
            
            # Score each domain
            domain_scores = {}
            for domain, keywords in domain_keywords.items():
                score = sum(1 for keyword in keywords if keyword in query_lower)
                domain_scores[domain] = score
            
            # Check CSV column names for additional context
            columns = data_context.get('columns', [])
            if columns:
                for domain, keywords in domain_keywords.items():
                    column_score = sum(1 for col in columns for keyword in keywords 
                                     if keyword.lower() in col.lower())
                    domain_scores[domain] += column_score * 0.5  # Weight column matches less
            
            # Return domain with highest score
            best_domain = max(domain_scores, key=domain_scores.get)
            return best_domain if domain_scores[best_domain] > 0 else 'general'
            
        except Exception as e:
            logging.error(f"Error identifying business domain: {e}")
            return 'general'
    
    def _extract_key_metrics(self, data_context: Dict[str, Any]) -> List[str]:
        """Extract key business metrics from data context"""
        try:
            metrics = []
            columns = data_context.get('columns', [])
            
            # Define metric patterns
            metric_patterns = {
                'revenue': ['revenue', 'sales', 'income', 'earnings'],
                'growth': ['growth', 'increase', 'change', 'trend'],
                'performance': ['performance', 'efficiency', 'productivity', 'success'],
                'customer': ['customer', 'client', 'user', 'account'],
                'cost': ['cost', 'expense', 'budget', 'spend'],
                'profit': ['profit', 'margin', 'roi', 'return']
            }
            
            for metric_type, patterns in metric_patterns.items():
                matching_columns = [col for col in columns 
                                  for pattern in patterns 
                                  if pattern.lower() in col.lower()]
                if matching_columns:
                    metrics.append(f"{metric_type.title()}: {', '.join(matching_columns[:3])}")
            
            return metrics[:5]  # Return top 5 metrics
            
        except Exception as e:
            logging.error(f"Error extracting key metrics: {e}")
            return ['Unable to extract metrics']
    
    def _analyze_growth_patterns(self, data_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze growth patterns from data"""
        try:
            growth_analysis = {
                'trend_direction': 'stable',
                'growth_rate': 0.0,
                'volatility': 'medium',
                'patterns': []
            }
            
            # Analyze DataFrames for growth patterns
            dataframes = data_context.get('dataframes', {})
            for df_name, df_info in dataframes.items():
                if isinstance(df_info, dict) and 'data' in df_info:
                    df = df_info['data']
                    if isinstance(df, pd.DataFrame):
                        # Look for time series data
                        date_columns = [col for col in df.columns 
                                      if any(date_indicator in col.lower() 
                                           for date_indicator in ['date', 'time', 'month', 'year'])]
                        
                        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
                        
                        if date_columns and numeric_columns:
                            growth_analysis['patterns'].append(
                                f"Time series data detected in {df_name} with {len(numeric_columns)} metrics"
                            )
                            
                            # Simple growth calculation for first numeric column
                            if len(df) > 1:
                                first_value = df[numeric_columns[0]].iloc[0]
                                last_value = df[numeric_columns[0]].iloc[-1]
                                if first_value != 0:
                                    growth_rate = ((last_value - first_value) / first_value) * 100
                                    growth_analysis['growth_rate'] = round(growth_rate, 2)
                                    
                                    if growth_rate > 5:
                                        growth_analysis['trend_direction'] = 'growing'
                                    elif growth_rate < -5:
                                        growth_analysis['trend_direction'] = 'declining'
            
            return growth_analysis
            
        except Exception as e:
            logging.error(f"Error analyzing growth patterns: {e}")
            return {'trend_direction': 'unknown', 'error': str(e)}
    
    def _assess_market_position(self, data_context: Dict[str, Any]) -> str:
        """Assess market position based on data patterns"""
        try:
            # Simple assessment based on data characteristics
            shape = data_context.get('shape', (0, 0))
            columns = data_context.get('columns', [])
            
            if shape[0] > 10000:
                return "Large-scale operations with extensive data coverage"
            elif shape[0] > 1000:
                return "Medium-scale operations with good data granularity"
            elif shape[0] > 100:
                return "Small to medium-scale operations"
            else:
                return "Limited data scope - early stage or niche focus"
                
        except Exception as e:
            return "Unable to assess market position"
    
    def _identify_risk_factors(self, query: str, data_context: Dict[str, Any]) -> List[str]:
        """Identify potential risk factors"""
        risk_factors = []
        
        # Query-based risk indicators
        risk_keywords = ['decline', 'decrease', 'loss', 'challenge', 'problem', 'issue', 'concern']
        query_lower = query.lower()
        
        for keyword in risk_keywords:
            if keyword in query_lower:
                risk_factors.append(f"Query indicates potential {keyword} in business metrics")
        
        # Data-based risk indicators
        dataframes = data_context.get('dataframes', {})
        for df_name, df_info in dataframes.items():
            if isinstance(df_info, dict) and 'data' in df_info:
                df = df_info['data']
                if isinstance(df, pd.DataFrame):
                    # Check for missing data
                    missing_percentage = (df.isnull().sum().sum() / (df.shape[0] * df.shape[1])) * 100
                    if missing_percentage > 20:
                        risk_factors.append(f"High missing data rate ({missing_percentage:.1f}%) in {df_name}")
        
        return risk_factors[:3]  # Return top 3 risk factors
    
    def _analyze_dataframe_trends(self, df: pd.DataFrame, df_name: str) -> List[str]:
        """Analyze trends in individual DataFrame"""
        trends = []
        
        try:
            # Check for numeric trends
            numeric_columns = df.select_dtypes(include=['number']).columns
            for col in numeric_columns[:3]:  # Analyze top 3 numeric columns
                if len(df) > 1:
                    values = df[col].dropna()
                    if len(values) > 1:
                        # Simple trend analysis
                        first_half = values[:len(values)//2].mean()
                        second_half = values[len(values)//2:].mean()
                        
                        if second_half > first_half * 1.1:
                            trends.append(f"Upward trend in {col} (+{((second_half/first_half - 1) * 100):.1f}%)")
                        elif second_half < first_half * 0.9:
                            trends.append(f"Downward trend in {col} (-{((1 - second_half/first_half) * 100):.1f}%)")
            
        except Exception as e:
            logging.error(f"Error analyzing DataFrame trends: {e}")
        
        return trends
    
    def _get_fallback_market_data(self, keywords: List[str]) -> Dict[str, Any]:
        """Fallback market data when GNews is not available"""
        return {
            'success': False,
            'articles': [],
            'total_found': 0,
            'query_keywords': keywords,
            'error': 'GNews API not available',
            'fallback_insights': [
                f"Monitor market trends related to: {', '.join(keywords[:5])}",
                "Consider external market factors affecting your business",
                "Stay informed about industry developments and competitive landscape",
                "Regular market research recommended for strategic planning"
            ],
            'timestamp': datetime.now().isoformat(),
            'source': 'fallback'
        }
    
    def _get_fallback_market_section(self) -> str:
        """Fallback market section when news data is not available"""
        return """
        <div class="market-intelligence-section">
            <h3>📰 Market Intelligence</h3>
            <div class="fallback-message">
                <p><em>Market intelligence data is currently unavailable.</em></p>
                <p>For comprehensive market insights, consider:</p>
                <ul>
                    <li>Monitoring industry news and trends</li>
                    <li>Analyzing competitive landscape</li>
                    <li>Tracking relevant market indicators</li>
                    <li>Regular market research and analysis</li>
                </ul>
            </div>
        </div>
        """
    
    def _format_date(self, date_string: str) -> str:
        """Format date string for display"""
        try:
            if not date_string:
                return "Date unknown"
            
            # Parse various date formats
            for fmt in ['%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                try:
                    dt = datetime.strptime(date_string, fmt)
                    return dt.strftime("%B %d, %Y")
                except ValueError:
                    continue
            
            return date_string  # Return original if parsing fails
            
        except Exception:
            return "Date unknown"
    
    def _get_sentiment_icon(self, sentiment: str) -> str:
        """Get emoji icon for sentiment"""
        sentiment_icons = {
            'positive': '📈',
            'negative': '📉',
            'neutral': '➡️'
        }
        return sentiment_icons.get(sentiment, '❓')
    
    @staticmethod
    def extract_business_keywords(user_query: str, csv_columns: List[str]) -> List[str]:
        """
        Extract business-relevant keywords from user query and CSV columns.
        
        Args:
            user_query: User's analysis query
            csv_columns: Column names from CSV data
            
        Returns:
            List of relevant keywords for market news search
        """
        try:
            keywords = set()
            
            # Extract from user query
            business_terms = [
                'sales', 'revenue', 'profit', 'growth', 'market', 'customer', 'product',
                'performance', 'trend', 'forecast', 'competition', 'industry', 'business',
                'financial', 'economic', 'commercial', 'strategic', 'operational'
            ]
            
            query_words = re.findall(r'\b\w+\b', user_query.lower())
            for word in query_words:
                if word in business_terms or len(word) > 4:  # Include longer words
                    keywords.add(word)
            
            # Extract from CSV columns
            for column in csv_columns:
                column_words = re.findall(r'\b\w+\b', column.lower())
                for word in column_words:
                    if word in business_terms or len(word) > 4:
                        keywords.add(word)
            
            # Filter and prioritize keywords
            filtered_keywords = []
            priority_terms = ['sales', 'revenue', 'profit', 'growth', 'market', 'customer']
            
            # Add priority terms first
            for term in priority_terms:
                if term in keywords:
                    filtered_keywords.append(term)
            
            # Add other relevant terms
            for keyword in keywords:
                if keyword not in filtered_keywords and keyword not in ['data', 'analysis', 'table']:
                    filtered_keywords.append(keyword)
            
            return filtered_keywords[:10]  # Return top 10 keywords
            
        except Exception as e:
            logging.error(f"Error extracting business keywords: {e}")
            return ['business', 'market', 'industry']  # Default fallback



# Enhanced HTML Report Generator Integration
class EnhancedHTMLReportGenerator:
    """
    Enhanced HTML Report Generator with market intelligence integration.
    Builds on the existing HTMLReportGenerator with comprehensive business reporting.
    """
    
    def __init__(self, session_id: str, output_dir: str = "reports"):
        self.session_id = session_id
        from pathlib import Path
        self.output_dir = output_dir
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.market_provider = MarketIntelligenceProvider()
        
    def generate_dynamic_report(self, analysis_results: Dict[str, Any], 
                               user_query: str, file_manager=None,
                               market_data: Dict[str, Any] = None) -> str:
        """
        Generate comprehensive dynamic report with market intelligence.
        
        Args:
            analysis_results: Results from assistant analysis
            user_query: Original user query
            file_manager: FileManager instance for downloading images
            market_data: Optional pre-fetched market data
            
        Returns:
            Path to generated HTML report
        """
        try:
            # Extract components from analysis results
            report_data = self._extract_comprehensive_report_components(
                analysis_results, file_manager
            )
            
            # Fetch market intelligence if not provided
            if market_data is None:
                market_data = self._fetch_market_intelligence_for_query(
                    user_query, report_data
                )
            
            # Generate AI-powered executive summary
            executive_summary = self._generate_executive_summary_with_ai(
                analysis_results, market_data
            )
            
            # Generate comprehensive HTML content
            html_content = self._generate_comprehensive_html_content(
                report_data, user_query, analysis_results, market_data, executive_summary
            )
            
            # Save report
            report_path = self._save_dynamic_report(html_content, user_query)
            
            logging.info(f"✅ Generated dynamic HTML report: {report_path}")
            return report_path
            
        except Exception as e:
            logging.error(f"❌ Error generating dynamic HTML report: {e}")
            raise
    
    def _extract_comprehensive_report_components(self, analysis_results: Dict[str, Any], 
                                               file_manager=None) -> Dict[str, Any]:
        """Extract and process all components for comprehensive report"""
        
        components = {
            'images': [],
            'dataframes': [],
            'code': analysis_results.get('generated_code', ''),
            'execution_outputs': analysis_results.get('execution_outputs', []),
            'summary': analysis_results.get('response_content', ''),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'analysis_type': analysis_results.get('type', 'analytical'),
            'success': analysis_results.get('success', False),
            'statistics': {}
        }
        
        # Process generated images with enhanced metadata
        generated_images = analysis_results.get('generated_images', [])
        for i, image_id in enumerate(generated_images):
            if file_manager:
                try:
                    temp_dir = self.output_dir / "temp_images"
                    temp_dir.mkdir(exist_ok=True)
                    
                    image_path = file_manager.download_generated_file(
                        image_id, str(temp_dir), f"chart_{image_id}.png"
                    )
                    
                    image_base64 = self._image_to_base64(image_path)
                    components['images'].append({
                        'id': image_id,
                        'base64': image_base64,
                        'path': image_path,
                        'title': f"Visualization {i+1}",
                        'description': self._generate_image_description(image_path)
                    })
                    
                except Exception as e:
                    logging.warning(f"⚠️ Could not process image {image_id}: {e}")
        
        # Extract and enhance dataframes
        components['dataframes'] = self._extract_enhanced_dataframes(
            analysis_results.get('dataframes', {})
        )
        
        # Generate statistics summary
        components['statistics'] = self._generate_statistics_summary(
            components['dataframes']
        )
        
        return components
    
    def _fetch_market_intelligence_for_query(self, user_query: str, 
                                           report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch market intelligence relevant to the query and data"""
        try:
            # Extract business keywords
            csv_columns = []
            for df_info in report_data.get('dataframes', []):
                if isinstance(df_info, dict) and 'columns' in df_info:
                    csv_columns.extend(df_info['columns'])
            
            keywords = MarketIntelligenceProvider.extract_business_keywords(
                user_query, csv_columns
            )
            
            # Fetch market news
            market_news = self.market_provider.fetch_market_news(keywords, limit=10)
            
            # Analyze trends
            market_trends = self.market_provider.extract_market_trends(
                user_query, {'dataframes': report_data.get('dataframes', {}), 'columns': csv_columns}
            )
            
            # Get industry context
            business_domain = market_trends.get('business_domain', 'general')
            industry_context = self.market_provider.get_industry_context(business_domain)
            
            return {
                'news': market_news,
                'trends': market_trends,
                'industry_context': industry_context,
                'business_domain': business_domain,
                'keywords_used': keywords,
                'fetch_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"❌ Error fetching market intelligence: {e}")
            return {
                'news': {'success': False, 'error': str(e)},
                'trends': {'error': str(e)},
                'industry_context': {},
                'business_domain': 'general',
                'keywords_used': [],
                'error': str(e)
            }
    
    def _generate_executive_summary_with_ai(self, analysis_results: Dict[str, Any], 
                                          market_context: Dict[str, Any]) -> str:
        """Generate AI-powered executive summary"""
        try:
            # Extract key findings from analysis
            key_findings = []
            
            # From DataFrames
            dataframes = analysis_results.get('dataframes', {})
            for df_name, df_info in dataframes.items():
                if isinstance(df_info, dict) and 'summary' in df_info:
                    summary = df_info['summary']
                    key_findings.append(
                        f"Generated {df_name} with {summary.get('rows', 0)} records"
                    )
            
            # From market intelligence
            market_trends = market_context.get('trends', {})
            business_domain = market_context.get('business_domain', 'general')
            
            # Construct executive summary
            executive_summary = f"""
            **Executive Summary**
            
            This analysis examined {business_domain} data patterns and generated {len(dataframes)} key datasets. 
            The analysis reveals {market_trends.get('trend_direction', 'stable')} trends with 
            {len(key_findings)} significant findings.
            
            **Key Insights:**
            • Data analysis generated actionable insights across {len(dataframes)} result datasets
            • Market sentiment appears {market_context.get('news', {}).get('articles', [{}])[0].get('sentiment', {}).get('label', 'neutral') if market_context.get('news', {}).get('articles') else 'neutral'}
            • Business domain identified as {business_domain} with relevant market factors
            
            **Strategic Implications:**
            The findings suggest focusing on data-driven decision making while monitoring 
            {business_domain} market developments. Consider implementing the generated 
            insights for operational improvements and strategic planning.
            """
            
            return executive_summary.strip()
            
        except Exception as e:
            logging.error(f"❌ Error generating executive summary: {e}")
            return """
            **Executive Summary**
            
            This comprehensive analysis has been completed successfully. The report includes
            detailed data analysis, visualizations, and strategic insights derived from your dataset.
            
            **Key Findings:**
            • Data analysis completed with generated insights and recommendations
            • Multiple analytical components have been processed and documented
            • Results are ready for strategic decision-making and operational planning
            
            **Next Steps:**
            Review the detailed analysis sections below for specific insights and actionable recommendations.
            """
    
    def _create_data_analysis_summary(self, dataframes: List[Dict], statistics: Dict) -> str:
        """Create comprehensive data analysis summary"""
        try:
            if not dataframes:
                return "<p>No structured data results generated in this analysis.</p>"
            
            summary_html = """
            <div class="data-analysis-summary">
                <h4>📊 Data Analysis Overview</h4>
                <div class="analysis-metrics">
            """
            
            total_rows = sum(df.get('summary', {}).get('rows', 0) for df in dataframes)
            total_columns = sum(df.get('summary', {}).get('columns', 0) for df in dataframes)
            
            summary_html += f"""
                    <div class="metric-card">
                        <h5>Generated Datasets</h5>
                        <span class="metric-value">{len(dataframes)}</span>
                        <span class="metric-label">DataFrames</span>
                    </div>
                    <div class="metric-card">
                        <h5>Total Records</h5>
                        <span class="metric-value">{total_rows:,}</span>
                        <span class="metric-label">Rows</span>
                    </div>
                    <div class="metric-card">
                        <h5>Data Points</h5>
                        <span class="metric-value">{total_columns}</span>
                        <span class="metric-label">Columns</span>
                    </div>
                </div>
                
                <h4>📋 Dataset Details</h4>
                <div class="datasets-overview">
            """
            
            for i, df_info in enumerate(dataframes, 1):
                df_name = df_info.get('name', f'Dataset {i}')
                shape = df_info.get('shape', (0, 0))
                columns = df_info.get('columns', [])
                
                summary_html += f"""
                    <div class="dataset-summary">
                        <h6>{df_name.replace('_', ' ').title()}</h6>
                        <p><strong>Dimensions:</strong> {shape[0]:,} rows × {shape[1]} columns</p>
                        <p><strong>Key Columns:</strong> {', '.join(columns[:5])}</p>
                        {f"<p><em>+{len(columns)-5} more columns</em></p>" if len(columns) > 5 else ""}
                    </div>
                """
            
            summary_html += """
                </div>
            </div>
            """
            
            return summary_html
            
        except Exception as e:
            logging.error(f"Error creating data analysis summary: {e}")
            return f"<p>Error generating data analysis summary: {str(e)}</p>"
    
    def _generate_trends_analysis(self, dataframes: List[Dict], time_series_data: Dict = None) -> str:
        """Generate trends analysis section"""
        try:
            trends_html = """
            <div class="trends-analysis">
                <h4>📈 Trends Analysis</h4>
            """
            
            # Analyze trends from dataframes
            trend_insights = []
            for df_info in dataframes:
                if isinstance(df_info, dict) and 'data' in df_info:
                    df = df_info['data']
                    if isinstance(df, pd.DataFrame) and len(df) > 1:
                        # Simple trend analysis
                        numeric_cols = df.select_dtypes(include=['number']).columns
                        for col in numeric_cols[:3]:  # Analyze top 3 numeric columns
                            values = df[col].dropna()
                            if len(values) > 1:
                                change = ((values.iloc[-1] - values.iloc[0]) / values.iloc[0] * 100)
                                trend_insights.append({
                                    'metric': col,
                                    'change_percent': round(change, 2),
                                    'direction': 'increasing' if change > 0 else 'decreasing',
                                    'dataset': df_info.get('name', 'Unknown')
                                })
            
            if trend_insights:
                trends_html += "<div class='trend-insights'>"
                for insight in trend_insights[:5]:  # Top 5 trends
                    direction_icon = "📈" if insight['direction'] == 'increasing' else "📉"
                    trends_html += f"""
                        <div class="trend-item">
                            <span class="trend-icon">{direction_icon}</span>
                            <span class="trend-metric">{insight['metric']}</span>
                            <span class="trend-change">{insight['change_percent']:+.1f}%</span>
                            <span class="trend-dataset">({insight['dataset']})</span>
                        </div>
                    """
                trends_html += "</div>"
            else:
                trends_html += "<p>No significant trends identified in the generated datasets.</p>"
            
            # Add forecasting insights if available
            if any('forecast' in df_info.get('name', '').lower() for df_info in dataframes):
                trends_html += """
                <div class="forecasting-insights">
                    <h5>🔮 Forecasting Insights</h5>
                    <p>Predictive models have been generated based on historical patterns. 
                    Review the forecast datasets for projected values and confidence intervals.</p>
                </div>
                """
            
            trends_html += "</div>"
            return trends_html
            
        except Exception as e:
            logging.error(f"Error generating trends analysis: {e}")
            return f"<div class='trends-analysis'><h4>📈 Trends Analysis</h4><p>Error: {str(e)}</p></div>"
    
    def _format_market_intelligence_section(self, market_data: Dict[str, Any], 
                                          news_data: Dict[str, Any]) -> str:
        """Format market intelligence section with news integration"""
        try:
            if not market_data or not news_data:
                return self.market_provider._get_fallback_market_section()
            
            # Use the market provider's formatting method
            news_html = self.market_provider.format_news_for_report(news_data)
            
            # Add additional market context
            business_domain = market_data.get('business_domain', 'general')
            industry_context = market_data.get('industry_context', {})
            
            additional_context = f"""
            <div class="industry-context">
                <h4>🏢 Industry Context: {business_domain.title()}</h4>
                <div class="context-grid">
                    <div class="context-item">
                        <h6>Key Metrics</h6>
                        <ul>
                            {self._format_list_items(industry_context.get('key_metrics', []))}
                        </ul>
                    </div>
                    <div class="context-item">
                        <h6>Growth Drivers</h6>
                        <ul>
                            {self._format_list_items(industry_context.get('growth_drivers', []))}
                        </ul>
                    </div>
                    <div class="context-item">
                        <h6>Market Factors</h6>
                        <ul>
                            {self._format_list_items(industry_context.get('market_factors', []))}
                        </ul>
                    </div>
                </div>
            </div>
            """
            
            return news_html + additional_context
            
        except Exception as e:
            logging.error(f"Error formatting market intelligence section: {e}")
            return self.market_provider._get_fallback_market_section()
    
    def _generate_ai_suggestions(self, analysis_results: Dict[str, Any], 
                               market_context: Dict[str, Any]) -> str:
        """Generate AI-powered strategic suggestions"""
        try:
            suggestions_html = """
            <div class="strategic-suggestions">
                <h4>💡 Strategic Suggestions</h4>
                <div class="suggestions-grid">
            """
            
            # Data-driven suggestions
            dataframes = analysis_results.get('dataframes', {})
            if dataframes:
                suggestions_html += """
                    <div class="suggestion-category">
                        <h5>📊 Data-Driven Recommendations</h5>
                        <ul>
                            <li>Leverage the generated datasets for regular monitoring and reporting</li>
                            <li>Implement automated analysis pipelines based on successful patterns</li>
                            <li>Consider expanding data collection to fill identified gaps</li>
                        </ul>
                    </div>
                """
            
            # Market-based suggestions
            business_domain = market_context.get('business_domain', 'general')
            market_trends = market_context.get('trends', {})
            
            if market_trends.get('trend_direction') == 'growing':
                suggestions_html += """
                    <div class="suggestion-category">
                        <h5>📈 Growth Opportunities</h5>
                        <ul>
                            <li>Capitalize on positive market trends identified in the analysis</li>
                            <li>Scale successful initiatives based on data insights</li>
                            <li>Invest in areas showing strong growth patterns</li>
                        </ul>
                    </div>
                """
            elif market_trends.get('trend_direction') == 'declining':
                suggestions_html += """
                    <div class="suggestion-category">
                        <h5>⚠️ Risk Mitigation</h5>
                        <ul>
                            <li>Address declining trends identified in the data analysis</li>
                            <li>Implement corrective measures for underperforming areas</li>
                            <li>Diversify strategies to reduce identified risks</li>
                        </ul>
                    </div>
                """
            
            # Technical suggestions
            suggestions_html += """
                <div class="suggestion-category">
                    <h5>🔧 Technical Implementation</h5>
                    <ul>
                        <li>Automate report generation for regular business reviews</li>
                        <li>Set up monitoring dashboards using generated insights</li>
                        <li>Integrate findings into existing business intelligence systems</li>
                    </ul>
                </div>
            """
            
            suggestions_html += """
                </div>
                
                <div class="next-steps">
                    <h5>🎯 Immediate Next Steps</h5>
                    <ol>
                        <li>Review and validate the generated datasets and insights</li>
                        <li>Share findings with relevant stakeholders and decision makers</li>
                        <li>Implement priority recommendations within the next 30 days</li>
                        <li>Schedule follow-up analysis to track progress and outcomes</li>
                    </ol>
                </div>
            </div>
            """
            
            return suggestions_html
            
        except Exception as e:
            logging.error(f"Error generating AI suggestions: {e}")
            return """
            <div class="strategic-suggestions">
                <h4>💡 Strategic Suggestions</h4>
                <p>Review the analysis results and consider how the insights can be applied to your business strategy.</p>
            </div>
            """
    
    def _generate_comprehensive_html_content(self, report_data: Dict[str, Any], 
                                           user_query: str, analysis_results: Dict[str, Any],
                                           market_data: Dict[str, Any], 
                                           executive_summary: str) -> str:
        """Generate comprehensive HTML content using professional template"""
        
        template_str = self._create_professional_html_template()
        
        # Prepare all sections
        data_summary = self._create_data_analysis_summary(
            report_data.get('dataframes', []), 
            report_data.get('statistics', {})
        )
        
        trends_analysis = self._generate_trends_analysis(
            report_data.get('dataframes', [])
        )
        
        market_intelligence = self._format_market_intelligence_section(
            market_data, market_data.get('news', {})
        )
        
        strategic_suggestions = self._generate_ai_suggestions(
            analysis_results, market_data
        )
        
        # Format dataframes as HTML tables
        dataframes_html = self._format_dataframes_as_tables(report_data.get('dataframes', []))
        
        # Format visualizations
        visualizations_html = self._format_visualizations(report_data.get('images', []))
        
        # Format code section
        code_html = self._format_code_section(report_data.get('code', ''))
        
        # Render template with all components
        from jinja2 import Template
        template = Template(template_str)
        
        return template.render(
            session_id=self.session_id,
            user_query=user_query,
            executive_summary=executive_summary,
            data_summary=data_summary,
            dataframes_html=dataframes_html,
            trends_analysis=trends_analysis,
            visualizations_html=visualizations_html,
            market_intelligence=market_intelligence,
            strategic_suggestions=strategic_suggestions,
            code_html=code_html,
            timestamp=report_data['timestamp'],
            analysis_type=report_data.get('analysis_type', 'comprehensive'),
            success=report_data.get('success', True)
        )
    
    def _create_professional_html_template(self) -> str:
        """Create professional consulting-style HTML template"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Strategic Data Analysis Report - {{ session_id }}</title>
    <style>
        /* Professional Consulting Firm Styling */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #2c3e50;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
        }
        
        .report-container {
            max-width: 1200px;
            margin: 20px auto;
            background: white;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            border-radius: 15px;
            overflow: hidden;
        }
        
        /* Cover Page Styling */
        .report-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 60px 40px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .report-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
            pointer-events: none;
        }
        
        .report-header h1 {
            font-size: 3em;
            font-weight: 300;
            margin-bottom: 20px;
            position: relative;
            z-index: 1;
        }
        
        .report-meta {
            background: rgba(255, 255, 255, 0.15);
            padding: 25px;
            border-radius: 10px;
            margin-top: 30px;
            backdrop-filter: blur(10px);
            position: relative;
            z-index: 1;
        }
        
        .report-meta-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            text-align: left;
        }
        
        .meta-item {
            display: flex;
            flex-direction: column;
        }
        
        .meta-label {
            font-size: 0.9em;
            opacity: 0.8;
            margin-bottom: 5px;
        }
        
        .meta-value {
            font-size: 1.1em;
            font-weight: 600;
        }
        
        /* Content Sections */
        .report-content {
            padding: 40px;
        }
        
        .section {
            margin-bottom: 50px;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 40px;
        }
        
        .section:last-child {
            border-bottom: none;
        }
        
        .section-title {
            color: #2c3e50;
            font-size: 2em;
            margin-bottom: 25px;
            border-left: 5px solid #3498db;
            padding-left: 20px;
            font-weight: 600;
        }
        
        .subsection-title {
            color: #34495e;
            font-size: 1.4em;
            margin: 25px 0 15px 0;
            font-weight: 500;
        }
        
        /* Executive Summary */
        .executive-summary {
            background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin: 30px 0;
            box-shadow: 0 8px 25px rgba(116, 185, 255, 0.3);
        }
        
        .executive-summary h3 {
            margin-bottom: 20px;
            font-size: 1.8em;
        }
        
        /* Data Analysis Cards */
        .analysis-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 25px 0;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #a29bfe 0%, #6c5ce7 100%);
            color: white;
            padding: 25px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(108, 92, 231, 0.3);
            transition: transform 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
        }
        
        .metric-value {
            display: block;
            font-size: 2.5em;
            font-weight: 700;
            margin: 10px 0;
        }
        
        .metric-label {
            display: block;
            font-size: 0.9em;
            opacity: 0.9;
        }
        
        /* Tables Styling */
        .dataframe-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 0.9em;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
            overflow: hidden;
        }
        
        .dataframe-table th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 12px;
            text-align: left;
            font-weight: 600;
        }
        
        .dataframe-table td {
            padding: 12px;
            border-bottom: 1px solid #ecf0f1;
        }
        
        .dataframe-table tbody tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        
        .dataframe-table tbody tr:hover {
            background-color: #e3f2fd;
        }
        
        /* Visualizations */
        .visualization-item {
            text-align: center;
            margin: 30px 0;
            padding: 25px;
            background: #fafbfc;
            border-radius: 12px;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
        }
        
        .chart-image {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.15);
        }
        
        .chart-description {
            margin-top: 15px;
            color: #666;
            font-style: italic;
        }
        
        /* Trends Analysis */
        .trend-insights {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .trend-item {
            background: white;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #3498db;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .trend-icon {
            font-size: 1.5em;
        }
        
        .trend-metric {
            font-weight: 600;
            flex: 1;
        }
        
        .trend-change {
            font-weight: 700;
            color: #27ae60;
        }
        
        .trend-change:contains('-') {
            color: #e74c3c;
        }
        
        /* Market Intelligence */
        .news-article {
            background: white;
            margin: 15px 0;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #3498db;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
        }
        .article-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            font-size: 0.9em;
            color: #666;
        }
        
        .article-title {
            color: #2c3e50;
            margin: 10px 0;
            font-size: 1.1em;
        }
        
        .sentiment-positive { color: #27ae60; font-weight: 600; }
        .sentiment-negative { color: #e74c3c; font-weight: 600; }
        .sentiment-neutral { color: #95a5a6; font-weight: 600; }
        
        /* Code Section */
        .code-section {
            background: #2c3e50;
            color: #ecf0f1;
            padding: 25px;
            border-radius: 10px;
            margin: 20px 0;
            overflow-x: auto;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 14px;
            line-height: 1.5;
        }
        
        .code-header {
            color: #3498db;
            margin-bottom: 15px;
            font-weight: 600;
        }
        
        /* Strategic Suggestions */
        .suggestions-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
            margin: 25px 0;
        }
        
        .suggestion-category {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            border-top: 4px solid #3498db;
        }
        
        .suggestion-category h5 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.2em;
        }
        
        .suggestion-category ul {
            list-style: none;
            padding: 0;
        }
        
        .suggestion-category li {
            padding: 8px 0;
            border-bottom: 1px solid #ecf0f1;
            position: relative;
            padding-left: 20px;
        }
        
        .suggestion-category li:before {
            content: '→';
            position: absolute;
            left: 0;
            color: #3498db;
            font-weight: bold;
        }
        
        .next-steps {
            background: linear-gradient(135deg, #fd79a8 0%, #e84393 100%);
            color: white;
            padding: 25px;
            border-radius: 12px;
            margin-top: 25px;
        }
        
        .next-steps h5 {
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        .next-steps ol {
            padding-left: 20px;
        }
        
        .next-steps li {
            margin: 8px 0;
            font-weight: 500;
        }
        
        /* Context Grid */
        .context-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .context-item {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #3498db;
        }
        
        .context-item h6 {
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        
        .context-item ul {
            list-style: none;
            padding: 0;
        }
        
        .context-item li {
            padding: 5px 0;
            padding-left: 15px;
            position: relative;
        }
        
        .context-item li:before {
            content: '•';
            position: absolute;
            left: 0;
            color: #3498db;
            font-weight: bold;
        }
        
        /* Print Styles */
        @media print {
            body {
                background: white;
            }
            
            .report-container {
                box-shadow: none;
                margin: 0;
            }
            
            .section {
                page-break-inside: avoid;
                margin-bottom: 30px;
            }
            
            .metric-card, .news-article, .suggestion-category {
                page-break-inside: avoid;
            }
        }
        
        /* Mobile Responsive */
        @media (max-width: 768px) {
            .report-header {
                padding: 40px 20px;
            }
            
            .report-header h1 {
                font-size: 2em;
            }
            
            .report-content {
                padding: 20px;
            }
            
            .section-title {
                font-size: 1.5em;
            }
            
            .analysis-metrics {
                grid-template-columns: 1fr;
            }
            
            .suggestions-grid {
                grid-template-columns: 1fr;
            }
        }
        
        /* Animation Effects */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .section {
            animation: fadeInUp 0.6s ease-out;
        }
        
        /* Table of Contents */
        .table-of-contents {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            margin: 30px 0;
        }
        
        .toc-title {
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.4em;
            font-weight: 600;
        }
        
        .toc-list {
            list-style: none;
            padding: 0;
        }
        
        .toc-item {
            padding: 8px 0;
            border-bottom: 1px dotted #bdc3c7;
        }
        
        .toc-item a {
            color: #3498db;
            text-decoration: none;
            font-weight: 500;
        }
        
        .toc-item a:hover {
            color: #2980b9;
            text-decoration: underline;
        }
        
        /* Additional utility classes */
        .highlight {
            background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
        }
        
        .info-box {
            background: #dff0d8;
            border: 1px solid #d6e9c6;
            color: #3c763d;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
        }
        
        .warning-box {
            background: #fcf8e3;
            border: 1px solid #faebcc;
            color: #8a6d3b;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
        }
        
        .error-box {
            background: #f2dede;
            border: 1px solid #ebccd1;
            color: #a94442;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
        }
    </style>
</head>
<body>
    <div class="report-container">
        <!-- Cover Page -->
        <div class="report-header">
            <h1>📊 Strategic Data Analysis Report</h1>
            <div class="report-meta">
                <div class="report-meta-grid">
                    <div class="meta-item">
                        <span class="meta-label">Session ID</span>
                        <span class="meta-value">{{ session_id }}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Generated</span>
                        <span class="meta-value">{{ timestamp }}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Analysis Type</span>
                        <span class="meta-value">{{ analysis_type.title() }}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Status</span>
                        <span class="meta-value">{% if success %}✅ Completed{% else %}⚠️ Partial{% endif %}</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="report-content">
            <!-- Table of Contents -->
            <div class="table-of-contents">
                <h3 class="toc-title">📋 Table of Contents</h3>
                <ul class="toc-list">
                    <li class="toc-item"><a href="#analysis-query">1. Analysis Query</a></li>
                    <li class="toc-item"><a href="#executive-summary">2. Executive Summary</a></li>
                    <li class="toc-item"><a href="#data-analysis">3. Data Analysis & Summary</a></li>
                    <li class="toc-item"><a href="#output-details">4. Output Details Data</a></li>
                    <li class="toc-item"><a href="#trends-analysis">5. Trends Analysis</a></li>
                    <li class="toc-item"><a href="#visualizations">6. Visualizations</a></li>
                    <li class="toc-item"><a href="#market-intelligence">7. Market Intelligence</a></li>
                    <li class="toc-item"><a href="#strategic-suggestions">8. Strategic Suggestions</a></li>
                    {% if code_html %}<li class="toc-item"><a href="#technical-appendix">9. Technical Appendix</a></li>{% endif %}
                </ul>
            </div>
            
            <!-- 1. Analysis Query -->
            <div class="section" id="analysis-query">
                <h2 class="section-title">🔍 Analysis Query</h2>
                <div class="highlight">
                    <strong>Original Request:</strong> "{{ user_query }}"
                </div>
            </div>
            
            <!-- 2. Executive Summary -->
            <div class="section" id="executive-summary">
                <h2 class="section-title">📋 Executive Summary</h2>
                <div class="executive-summary">
                    {{ executive_summary | replace('\n', '<br>') | safe }}
                </div>
            </div>
            
            <!-- 3. Data Analysis & Summary -->
            <div class="section" id="data-analysis">
                <h2 class="section-title">📊 Data Analysis & Summary</h2>
                {{ data_summary | safe }}
            </div>
            
            <!-- 4. Output Details Data -->
            <div class="section" id="output-details">
                <h2 class="section-title">📈 Output Details Data</h2>
                {% if dataframes_html %}
                    {{ dataframes_html | safe }}
                {% else %}
                    <div class="info-box">
                        <p>No structured data outputs were generated in this analysis. The analysis focused on insights and recommendations rather than data transformation.</p>
                    </div>
                {% endif %}
            </div>
            
            <!-- 5. Trends Analysis -->
            <div class="section" id="trends-analysis">
                <h2 class="section-title">📈 Trends Analysis</h2>
                {{ trends_analysis | safe }}
            </div>
            
            <!-- 6. Visualizations -->
            <div class="section" id="visualizations">
                <h2 class="section-title">📊 Visualizations</h2>
                {% if visualizations_html %}
                    {{ visualizations_html | safe }}
                {% else %}
                    <div class="info-box">
                        <p>No visualizations were generated for this analysis. Consider requesting charts or graphs for visual data exploration.</p>
                    </div>
                {% endif %}
            </div>
            
            <!-- 7. Market Intelligence -->
            <div class="section" id="market-intelligence">
                <h2 class="section-title">📰 Market Intelligence</h2>
                {{ market_intelligence | safe }}
            </div>
            
            <!-- 8. Strategic Suggestions -->
            <div class="section" id="strategic-suggestions">
                <h2 class="section-title">💡 Strategic Suggestions</h2>
                {{ strategic_suggestions | safe }}
            </div>
            
            <!-- 9. Technical Appendix (if code exists) -->
            {% if code_html %}
            <div class="section" id="technical-appendix">
                <h2 class="section-title">💻 Technical Appendix</h2>
                {{ code_html | safe }}
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
        """
    
    def _extract_enhanced_dataframes(self, dataframes_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract and enhance dataframes with metadata"""
        enhanced_dataframes = []
        
        try:
            for df_name, df_info in dataframes_data.items():
                enhanced_df = {
                    'name': df_name,
                    'display_name': df_name.replace('_', ' ').title()
                }
                
                if isinstance(df_info, dict):
                    enhanced_df.update({
                        'shape': df_info.get('shape', (0, 0)),
                        'columns': df_info.get('columns', []),
                        'summary': df_info.get('summary', {}),
                        'data': df_info.get('data'),
                        'type': df_info.get('type', 'dataframe')
                    })
                elif isinstance(df_info, pd.DataFrame):
                    enhanced_df.update({
                        'shape': df_info.shape,
                        'columns': list(df_info.columns),
                        'data': df_info,
                        'type': 'dataframe',
                        'summary': {
                            'rows': len(df_info),
                            'columns': len(df_info.columns),
                            'memory_usage': df_info.memory_usage(deep=True).sum()
                        }
                    })
                
                enhanced_dataframes.append(enhanced_df)
                
        except Exception as e:
            logging.error(f"Error extracting enhanced dataframes: {e}")
        
        return enhanced_dataframes
    
    def _generate_statistics_summary(self, dataframes: List[Dict]) -> Dict[str, Any]:
        """Generate comprehensive statistics summary"""
        try:
            stats = {
                'total_dataframes': len(dataframes),
                'total_rows': 0,
                'total_columns': 0,
                'data_types': {},
                'memory_usage': 0
            }
            
            for df_info in dataframes:
                if isinstance(df_info, dict):
                    summary = df_info.get('summary', {})
                    stats['total_rows'] += summary.get('rows', 0)
                    stats['total_columns'] += summary.get('columns', 0)
                    stats['memory_usage'] += summary.get('memory_usage', 0)
            
            return stats
            
        except Exception as e:
            logging.error(f"Error generating statistics summary: {e}")
            return {'total_dataframes': 0, 'error': str(e)}
    
    def _format_dataframes_as_tables(self, dataframes: List[Dict]) -> str:
        """Format dataframes as styled HTML tables"""
        try:
            if not dataframes:
                return "<p>No data tables were generated in this analysis.</p>"
            
            tables_html = ""
            
            for df_info in dataframes:
                df_name = df_info.get('display_name', df_info.get('name', 'Unknown Dataset'))
                df_data = df_info.get('data')
                
                if isinstance(df_data, pd.DataFrame) and not df_data.empty:
                    # Generate table HTML
                    table_html = df_data.head(20).to_html(
                        classes="dataframe-table",
                        index=False,
                        escape=False
                    )
                    
                    tables_html += f"""
                    <div class="dataframe-section">
                        <h4>{df_name}</h4>
                        <div class="table-metadata">
                            <span><strong>Shape:</strong> {df_data.shape[0]:,} rows × {df_data.shape[1]} columns</span>
                            <span class="separator">|</span>
                            <span><strong>Memory:</strong> {df_data.memory_usage(deep=True).sum() / 1024:.1f} KB</span>
                        </div>
                        <div class="table-container">
                            {table_html}
                        </div>
                        {f'<p class="table-note"><em>Showing first 20 rows of {len(df_data):,} total rows.</em></p>' if len(df_data) > 20 else ''}
                    </div>
                    """
            
            return tables_html
            
        except Exception as e:
            logging.error(f"Error formatting dataframes as tables: {e}")
            return f"<p>Error formatting data tables: {str(e)}</p>"
    
    def _format_visualizations(self, images: List[Dict]) -> str:
        """Format visualizations section"""
        try:
            if not images:
                return "<p>No visualizations were generated for this analysis.</p>"
            
            viz_html = ""
            
            for i, image_info in enumerate(images, 1):
                title = image_info.get('title', f'Visualization {i}')
                description = image_info.get('description', 'Analysis visualization')
                base64_data = image_info.get('base64', '')
                
                if base64_data:
                    viz_html += f"""
                    <div class="visualization-item">
                        <h4>{title}</h4>
                        <img src="data:image/png;base64,{base64_data}" 
                             alt="{title}" class="chart-image">
                        <div class="chart-description">{description}</div>
                    </div>
                    """
            
            return viz_html
            
        except Exception as e:
            logging.error(f"Error formatting visualizations: {e}")
            return f"<p>Error formatting visualizations: {str(e)}</p>"
    
    def _format_code_section(self, code: str) -> str:
        """Format code section for report"""
        try:
            if isinstance(code, dict):
                code_content = code.get('code', '')
            else:
                code_content = str(code) if code else ''
            
            if not code_content.strip():
                return ""
            
            return f"""
            <div class="code-section">
                <div class="code-header">Generated Python Code</div>
                <pre><code>{code_content}</code></pre>
                <div style="margin-top: 15px; font-size: 0.9em; opacity: 0.8;">
                    <strong>Code Statistics:</strong> {len(code_content.splitlines())} lines, 
                    {len(code_content)} characters
                </div>
            </div>
        """

        except Exception as e:
            logging.error(f"Error formatting code section: {e}")
            return ""
    
    def _image_to_base64(self, image_path: str) -> str:
        """Convert image file to base64 string"""
        try:
            import base64
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
                return base64.b64encode(image_data).decode('utf-8')
        except Exception as e:
            logging.warning(f"⚠️ Could not convert image to base64: {e}")
            return ""
    
    def _generate_image_description(self, image_path: str) -> str:
        """Generate description for image based on filename and context"""
        try:
            
            filename = Path(image_path).stem
            
            # Generate description based on filename patterns
            if 'forecast' in filename.lower():
                return "Predictive analysis showing projected values and trends"
            elif 'trend' in filename.lower():
                return "Trend analysis visualization showing patterns over time"
            elif 'comparison' in filename.lower():
                return "Comparative analysis between different categories or time periods"
            elif 'distribution' in filename.lower():
                return "Distribution analysis showing data spread and patterns"
            else:
                return "Data visualization generated from analysis results"
                
        except Exception as e:
            return "Analysis visualization"
    
    def _format_list_items(self, items: List[str]) -> str:
        """Format list items for HTML"""
        if not items:
            return "<li>No items available</li>"
        
        return "".join(f"<li>{item.replace('_', ' ').title()}</li>" for item in items[:5])
    
    def _save_dynamic_report(self, html_content: str, user_query: str) -> str:
        """Save dynamic HTML report with descriptive filename"""
        try:
            # Create descriptive filename
            query_words = re.findall(r'\b\w+\b', user_query.lower())
            query_summary = "_".join(query_words[:3]) if query_words else "analysis"
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dynamic_report_{query_summary}_{self.session_id}_{timestamp}.html"
            
            # Clean filename
            filename = re.sub(r'[^\w\-_\.]', '_', filename)
            report_path = self.output_dir / filename
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return str(report_path)
        except Exception as e:
            logging.error(f"Error saving dynamic report: {e}")
            # Fallback filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dynamic_report_{self.session_id}_{timestamp}.html"
            report_path = self.output_dir / filename
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return str(report_path)
    
    def cleanup_temp_files(self):
        """Clean up temporary files generated during report creation"""
        try:
            temp_dir = self.output_dir / "temp_images"
            if temp_dir.exists():
                for file_path in temp_dir.iterdir():
                    try:
                        file_path.unlink()
                        logging.info(f"🗑️ Deleted temp file: {file_path}")
                    except Exception as e:
                        logging.warning(f"⚠️ Could not delete temp file {file_path}: {e}")
                
                # Remove empty temp directory
                try:
                    temp_dir.rmdir()
                    logging.info(f"🗑️ Removed temp directory: {temp_dir}")
                except Exception as e:
                    logging.warning(f"⚠️ Could not remove temp directory: {e}")
                    
        except Exception as e:
            logging.error(f"❌ Error during temp files cleanup: {e}")
    
  
     