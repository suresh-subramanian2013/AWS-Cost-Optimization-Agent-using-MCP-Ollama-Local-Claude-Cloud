"""
AWS Cost Explorer and Billing API wrapper.
Provides methods for retrieving cost data, forecasts, anomalies, and optimization recommendations.
"""
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError, BotoCoreError
import logging

from config import Config

logger = logging.getLogger(__name__)


class AWSCostService:
    """AWS Cost Explorer and Billing service wrapper."""
    
    def __init__(self):
        """Initialize AWS clients."""
        self.ce_client = boto3.client(
            'ce',
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            region_name=Config.AWS_DEFAULT_REGION
        )
        
        self.cost_optimization_hub_client = boto3.client(
            'cost-optimization-hub',
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            region_name=Config.AWS_DEFAULT_REGION
        )
    
    def get_cost_and_usage(
        self,
        start_date: str,
        end_date: str,
        granularity: str = "DAILY",
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get cost and usage data for a specified time period.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            granularity: DAILY, MONTHLY, or HOURLY
            metrics: List of metrics (default: ["UnblendedCost"])
        
        Returns:
            Cost and usage data
        """
        if metrics is None:
            metrics = ["UnblendedCost"]
        
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity=granularity,
                Metrics=metrics,
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )
            return response
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Error retrieving cost and usage: {e}")
            raise
    
    def get_cost_forecast(
        self,
        start_date: str,
        end_date: str,
        metric: str = "UNBLENDED_COST"
    ) -> Dict[str, Any]:
        """
        Get cost forecast for future periods.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            metric: Forecast metric (default: UNBLENDED_COST)
        
        Returns:
            Cost forecast data
        """
        try:
            response = self.ce_client.get_cost_forecast(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Metric=metric,
                Granularity='DAILY'
            )
            return response
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Error retrieving cost forecast: {e}")
            raise
    
    def get_cost_anomalies(
        self,
        start_date: str,
        end_date: str,
        max_results: int = 100
    ) -> Dict[str, Any]:
        """
        Detect unusual spending patterns.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            max_results: Maximum number of anomalies to return
        
        Returns:
            Cost anomaly data
        """
        try:
            response = self.ce_client.get_anomalies(
                DateInterval={
                    'StartDate': start_date,
                    'EndDate': end_date
                },
                MaxResults=max_results
            )
            return response
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Error retrieving cost anomalies: {e}")
            raise
    
    def get_service_costs(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Break down costs by AWS service.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
        
        Returns:
            Service-level cost breakdown
        """
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )
            return response
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Error retrieving service costs: {e}")
            raise
    
    def get_optimization_recommendations(
        self,
        max_results: int = 100
    ) -> Dict[str, Any]:
        """
        Fetch AWS Cost Explorer optimization recommendations.
        
        Args:
            max_results: Maximum number of recommendations to return
        
        Returns:
            Optimization recommendations
        """
        try:
            # Get rightsizing recommendations
            rightsizing_response = self.ce_client.get_rightsizing_recommendation(
                Service='AmazonEC2',
                Configuration={
                    'RecommendationTarget': 'SAME_INSTANCE_FAMILY',
                    'BenefitsConsidered': True
                }
            )
            
            # Get Savings Plans recommendations
            savings_plans_response = self.ce_client.get_savings_plans_purchase_recommendation(
                SavingsPlansType='COMPUTE_SP',
                TermInYears='ONE_YEAR',
                PaymentOption='NO_UPFRONT',
                LookbackPeriodInDays='THIRTY_DAYS'
            )
            
            return {
                'rightsizing': rightsizing_response,
                'savings_plans': savings_plans_response
            }
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Error retrieving optimization recommendations: {e}")
            raise
    
    @staticmethod
    def get_date_range(days_back: int = 30) -> tuple[str, str]:
        """
        Get date range for the last N days.
        
        Args:
            days_back: Number of days to look back
        
        Returns:
            Tuple of (start_date, end_date) in YYYY-MM-DD format
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
