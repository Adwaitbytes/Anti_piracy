from datetime import datetime, timedelta
from typing import List, Dict, Any
import numpy as np
from sqlalchemy import create_engine, text
from dataclasses import dataclass
import json
import logging

@dataclass
class AnalyticsData:
    detection_trend: List[Dict[str, Any]]
    content_types: List[Dict[str, Any]]
    violations_by_platform: List[Dict[str, Any]]
    detection_accuracy: List[Dict[str, Any]]

class AnalyticsEngine:
    """Analytics engine for processing and aggregating piracy detection data."""
    
    def __init__(self, db_url: str):
        """
        Initialize analytics engine.
        
        Args:
            db_url: Database connection URL
        """
        self.engine = create_engine(db_url)
        self.logger = logging.getLogger(__name__)

    def get_analytics(self, time_range: str) -> AnalyticsData:
        """
        Get analytics data for specified time range.
        
        Args:
            time_range: Time range (24h, 7d, 30d, 90d)
            
        Returns:
            AnalyticsData object containing all analytics
        """
        end_date = datetime.utcnow()
        
        if time_range == '24h':
            start_date = end_date - timedelta(days=1)
        elif time_range == '7d':
            start_date = end_date - timedelta(days=7)
        elif time_range == '30d':
            start_date = end_date - timedelta(days=30)
        else:  # 90d
            start_date = end_date - timedelta(days=90)
            
        return AnalyticsData(
            detection_trend=self._get_detection_trend(start_date, end_date),
            content_types=self._get_content_types(start_date, end_date),
            violations_by_platform=self._get_violations_by_platform(start_date, end_date),
            detection_accuracy=self._get_detection_accuracy(start_date, end_date)
        )

    def _get_detection_trend(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get trend of detections over time."""
        try:
            query = text("""
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as total_scans,
                    SUM(CASE WHEN is_violation = true THEN 1 ELSE 0 END) as violations
                FROM detection_results
                WHERE timestamp BETWEEN :start_date AND :end_date
                GROUP BY DATE(timestamp)
                ORDER BY date
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(
                    query,
                    {"start_date": start_date, "end_date": end_date}
                )
                return [
                    {
                        "date": row.date.strftime("%Y-%m-%d"),
                        "scans": row.total_scans,
                        "violations": row.violations
                    }
                    for row in result
                ]
        except Exception as e:
            self.logger.error(f"Error getting detection trend: {str(e)}")
            return []

    def _get_content_types(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get distribution of protected content types."""
        try:
            query = text("""
                SELECT 
                    content_type,
                    COUNT(*) as count
                FROM protected_content
                WHERE registration_date BETWEEN :start_date AND :end_date
                GROUP BY content_type
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(
                    query,
                    {"start_date": start_date, "end_date": end_date}
                )
                return [
                    {"name": row.content_type, "value": row.count}
                    for row in result
                ]
        except Exception as e:
            self.logger.error(f"Error getting content types: {str(e)}")
            return []

    def _get_violations_by_platform(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get distribution of violations across platforms."""
        try:
            query = text("""
                SELECT 
                    platform,
                    COUNT(*) as violations
                FROM detection_results
                WHERE 
                    timestamp BETWEEN :start_date AND :end_date
                    AND is_violation = true
                GROUP BY platform
                ORDER BY violations DESC
                LIMIT 10
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(
                    query,
                    {"start_date": start_date, "end_date": end_date}
                )
                return [
                    {
                        "platform": row.platform,
                        "violations": row.violations
                    }
                    for row in result
                ]
        except Exception as e:
            self.logger.error(f"Error getting violations by platform: {str(e)}")
            return []

    def _get_detection_accuracy(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Calculate detection accuracy metrics over time."""
        try:
            query = text("""
                SELECT 
                    DATE(timestamp) as date,
                    AVG(confidence) * 100 as accuracy,
                    SUM(CASE WHEN is_false_positive = true THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as false_positive_rate
                FROM detection_results
                WHERE timestamp BETWEEN :start_date AND :end_date
                GROUP BY DATE(timestamp)
                ORDER BY date
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(
                    query,
                    {"start_date": start_date, "end_date": end_date}
                )
                return [
                    {
                        "date": row.date.strftime("%Y-%m-%d"),
                        "accuracy": round(row.accuracy, 2),
                        "falsePositives": round(row.false_positive_rate, 2)
                    }
                    for row in result
                ]
        except Exception as e:
            self.logger.error(f"Error getting detection accuracy: {str(e)}")
            return []

    def generate_report(self, time_range: str) -> Dict[str, Any]:
        """
        Generate comprehensive analytics report.
        
        Args:
            time_range: Time range for report
            
        Returns:
            Report data dictionary
        """
        analytics = self.get_analytics(time_range)
        
        # Calculate summary statistics
        total_scans = sum(day['scans'] for day in analytics.detection_trend)
        total_violations = sum(day['violations'] for day in analytics.detection_trend)
        avg_accuracy = np.mean([day['accuracy'] for day in analytics.detection_accuracy])
        
        return {
            "summary": {
                "total_scans": total_scans,
                "total_violations": total_violations,
                "average_accuracy": round(avg_accuracy, 2),
                "time_range": time_range
            },
            "trends": {
                "detection_trend": analytics.detection_trend,
                "content_types": analytics.content_types,
                "violations_by_platform": analytics.violations_by_platform,
                "detection_accuracy": analytics.detection_accuracy
            }
        }
