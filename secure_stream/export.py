from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
import io
import base64
import logging
from dataclasses import dataclass

@dataclass
class ExportConfig:
    include_analytics: bool = True
    include_history: bool = True
    include_violations: bool = True
    chart_style: str = "darkgrid"
    company_logo: Optional[str] = None

class ReportGenerator:
    """Generates comprehensive PDF reports for content protection data."""
    
    def __init__(self, config: ExportConfig):
        """
        Initialize report generator.
        
        Args:
            config: Export configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Set up plotting style
        sns.set_style(config.chart_style)
        plt.style.use('seaborn')

    def generate_content_report(
        self,
        content_id: str,
        content_data: Dict[str, Any],
        history_data: List[Dict[str, Any]],
        analytics_data: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Generate comprehensive PDF report for content.
        
        Args:
            content_id: Content identifier
            content_data: Basic content information
            history_data: Content history data
            analytics_data: Optional analytics data
            
        Returns:
            PDF report as bytes
        """
        try:
            # Create PDF
            pdf = FPDF()
            
            # Add title page
            self._add_title_page(pdf, content_data)
            
            # Add content overview
            self._add_content_overview(pdf, content_data)
            
            # Add protection history
            if self.config.include_history:
                self._add_history_section(pdf, history_data)
            
            # Add violation analysis
            if self.config.include_violations:
                self._add_violation_analysis(pdf, history_data)
            
            # Add analytics
            if self.config.include_analytics and analytics_data:
                self._add_analytics_section(pdf, analytics_data)
            
            # Return PDF bytes
            return pdf.output(dest='S').encode('latin1')
            
        except Exception as e:
            self.logger.error(f"Failed to generate report: {str(e)}")
            raise

    def _add_title_page(self, pdf: FPDF, content_data: Dict[str, Any]):
        """Add report title page."""
        pdf.add_page()
        
        # Add logo if configured
        if self.config.company_logo:
            pdf.image(self.config.company_logo, x=10, y=10, w=30)
        
        # Title
        pdf.set_font('Arial', 'B', 24)
        pdf.cell(0, 60, 'Content Protection Report', ln=True, align='C')
        
        # Content details
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, f"Content: {content_data['title']}", ln=True, align='C')
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f"Owner: {content_data['owner']}", ln=True, align='C')
        pdf.cell(0, 10, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", ln=True, align='C')

    def _add_content_overview(self, pdf: FPDF, content_data: Dict[str, Any]):
        """Add content overview section."""
        pdf.add_page()
        
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Content Overview', ln=True)
        
        pdf.set_font('Arial', '', 12)
        details = [
            ('Content ID', content_data.get('id', 'N/A')),
            ('Type', content_data.get('content_type', 'N/A')),
            ('Registration Date', content_data.get('registration_date', 'N/A')),
            ('Protection Status', content_data.get('status', 'N/A')),
            ('Description', content_data.get('description', 'N/A'))
        ]
        
        for key, value in details:
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(50, 10, key + ':', 0)
            pdf.set_font('Arial', '', 12)
            pdf.cell(0, 10, str(value), ln=True)

    def _add_history_section(self, pdf: FPDF, history_data: List[Dict[str, Any]]):
        """Add protection history section."""
        pdf.add_page()
        
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Protection History', ln=True)
        
        # Create timeline
        pdf.set_font('Arial', '', 12)
        for event in history_data:
            pdf.cell(40, 10, event['timestamp'][:10], 0)
            pdf.cell(30, 10, event['type'], 0)
            pdf.multi_cell(0, 10, event['details'])
            pdf.ln(5)

    def _add_violation_analysis(self, pdf: FPDF, history_data: List[Dict[str, Any]]):
        """Add violation analysis section with charts."""
        pdf.add_page()
        
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Violation Analysis', ln=True)
        
        # Filter violation events
        violations = [
            event for event in history_data 
            if event['type'] == 'violation'
        ]
        
        if not violations:
            pdf.set_font('Arial', '', 12)
            pdf.cell(0, 10, 'No violations detected', ln=True)
            return
        
        # Create violation trend chart
        fig, ax = plt.subplots(figsize=(10, 6))
        
        dates = [v['timestamp'][:10] for v in violations]
        platforms = [v['platform'] for v in violations]
        
        violation_df = pd.DataFrame({
            'date': dates,
            'platform': platforms
        })
        
        violation_counts = violation_df.groupby('date').size()
        
        ax.plot(violation_counts.index, violation_counts.values, marker='o')
        ax.set_title('Violation Trend')
        ax.set_xlabel('Date')
        ax.set_ylabel('Number of Violations')
        plt.xticks(rotation=45)
        
        # Save plot to bytes
        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format='png', bbox_inches='tight')
        img_bytes.seek(0)
        
        # Add chart to PDF
        pdf.image(img_bytes, x=10, y=None, w=190)
        plt.close()
        
        # Add violation details table
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Violation Details', ln=True)
        
        # Table headers
        headers = ['Date', 'Platform', 'Confidence', 'Status']
        col_widths = [40, 50, 40, 40]
        
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, header, 1)
        pdf.ln()
        
        # Table data
        pdf.set_font('Arial', '', 12)
        for violation in violations:
            pdf.cell(40, 10, violation['timestamp'][:10], 1)
            pdf.cell(50, 10, violation['platform'], 1)
            pdf.cell(40, 10, f"{violation['confidence']}%", 1)
            pdf.cell(40, 10, violation['status'], 1)
            pdf.ln()

    def _add_analytics_section(self, pdf: FPDF, analytics_data: Dict[str, Any]):
        """Add analytics section with insights."""
        pdf.add_page()
        
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Analytics & Insights', ln=True)
        
        # Protection effectiveness
        effectiveness = analytics_data.get('protection_effectiveness', {})
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 15, 'Protection Effectiveness', ln=True)
        
        metrics = [
            ('Detection Rate', f"{effectiveness.get('detection_rate', 0)}%"),
            ('False Positive Rate', f"{effectiveness.get('false_positive_rate', 0)}%"),
            ('Average Response Time', f"{effectiveness.get('avg_response_time', 0)} minutes")
        ]
        
        for key, value in metrics:
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(80, 10, key + ':', 0)
            pdf.set_font('Arial', '', 12)
            pdf.cell(0, 10, value, ln=True)
        
        # Create platform distribution chart
        if 'platform_distribution' in analytics_data:
            plt.figure(figsize=(10, 6))
            platforms = analytics_data['platform_distribution']
            plt.pie(
                [p['value'] for p in platforms],
                labels=[p['platform'] for p in platforms],
                autopct='%1.1f%%'
            )
            plt.title('Violation Distribution by Platform')
            
            # Save plot to bytes
            img_bytes = io.BytesIO()
            plt.savefig(img_bytes, format='png', bbox_inches='tight')
            img_bytes.seek(0)
            
            # Add chart to PDF
            pdf.image(img_bytes, x=10, y=None, w=190)
            plt.close()

class ExportService:
    """Manages export operations for content protection data."""
    
    def __init__(self, config: ExportConfig):
        """
        Initialize export service.
        
        Args:
            config: Export configuration
        """
        self.config = config
        self.report_generator = ReportGenerator(config)
        self.logger = logging.getLogger(__name__)

    async def export_content_report(
        self,
        content_id: str,
        include_analytics: bool = True
    ) -> bytes:
        """
        Generate and export content report.
        
        Args:
            content_id: Content identifier
            include_analytics: Whether to include analytics
            
        Returns:
            Report PDF as bytes
        """
        try:
            # Fetch content data
            content_data = await self._fetch_content_data(content_id)
            
            # Fetch history data
            history_data = await self._fetch_history_data(content_id)
            
            # Fetch analytics if requested
            analytics_data = None
            if include_analytics:
                analytics_data = await self._fetch_analytics_data(content_id)
            
            # Generate report
            return self.report_generator.generate_content_report(
                content_id,
                content_data,
                history_data,
                analytics_data
            )
            
        except Exception as e:
            self.logger.error(f"Failed to export content report: {str(e)}")
            raise

    async def _fetch_content_data(self, content_id: str) -> Dict[str, Any]:
        """Fetch basic content information."""
        # Implementation depends on data storage
        pass

    async def _fetch_history_data(
        self, content_id: str
    ) -> List[Dict[str, Any]]:
        """Fetch content history data."""
        # Implementation depends on data storage
        pass

    async def _fetch_analytics_data(
        self, content_id: str
    ) -> Dict[str, Any]:
        """Fetch analytics data for content."""
        # Implementation depends on data storage
        pass
