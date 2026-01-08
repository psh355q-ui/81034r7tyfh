"""
Daily Report Scheduler Service.

Automated daily report generation for AI Trading System.

Features:
- Daily scheduled report generation (7:10 AM)
- Error recovery with retry logic
- Performance monitoring
- Daily/Weekly/Monthly report generation
- Markdown export to docs/

Author: AI Trading System Team
Date: 2026-01-08
"""

import logging
import asyncio
import os
from datetime import datetime, time, timedelta, date
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession

from backend.reporting.report_generator import ReportGenerator
from backend.core.database import get_db

logger = logging.getLogger(__name__)


@dataclass
class ReportGenerationStats:
    """Statistics for report generation."""
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    report_type: str = ""  # "daily", "weekly", "monthly"
    report_date: Optional[date] = None
    success: bool = False
    error_message: Optional[str] = None
    file_path: Optional[str] = None
    
    @property
    def duration_seconds(self) -> float:
        """Calculate duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "report_type": self.report_type,
            "report_date": self.report_date.isoformat() if self.report_date else None,
            "success": self.success,
            "error_message": self.error_message,
            "file_path": self.file_path
        }


class DailyReportScheduler:
    """
    Automated daily report generator.
    
    Features:
    - Daily reports at 7:10 AM
    - Weekly reports on Monday at 7:15 AM
    - Monthly reports on 1st at 7:20 AM
    - Markdown export to docs/ folder
    - Error recovery
    
    Usage:
        scheduler = DailyReportScheduler()
        scheduler.start()
    """
    
    def __init__(
        self,
        daily_time: time = time(hour=7, minute=10),
        weekly_time: time = time(hour=7, minute=15),
        monthly_time: time = time(hour=7, minute=20),
        docs_dir: str = "docs",
        max_retries: int = 3,
        retry_delay_seconds: int = 60
    ):
        """
        Initialize daily report scheduler.
        
        Args:
            daily_time: Time to generate daily report (default: 7:10 AM)
            weekly_time: Time to generate weekly report (default: 7:15 AM Monday)
            monthly_time: Time to generate monthly report (default: 7:20 AM 1st)
            docs_dir: Directory to save reports (default: "docs")
            max_retries: Maximum retry attempts for failed generation
            retry_delay_seconds: Delay between retries in seconds
        """
        self.daily_time = daily_time
        self.weekly_time = weekly_time
        self.monthly_time = monthly_time
        self.docs_dir = docs_dir
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        
        self.scheduler = AsyncIOScheduler()
        self.last_daily_stats: Optional[ReportGenerationStats] = None
        self.last_weekly_stats: Optional[ReportGenerationStats] = None
        self.last_monthly_stats: Optional[ReportGenerationStats] = None
        self.is_running = False
        
        logger.info(
            f"DailyReportScheduler initialized: "
            f"daily={daily_time}, weekly={weekly_time}, monthly={monthly_time}"
        )
    
    def start(self):
        """Start the scheduler."""
        if self.is_running:
            logger.warning("Report scheduler is already running")
            return
        
        # Schedule daily report (every day at 7:10 AM)
        self.scheduler.add_job(
            self._generate_daily_report,
            trigger=CronTrigger(
                hour=self.daily_time.hour,
                minute=self.daily_time.minute
            ),
            id="daily_report_generation",
            name="Daily Report Generation",
            replace_existing=True
        )
        
        # Schedule weekly report (every Monday at 7:15 AM)
        self.scheduler.add_job(
            self._generate_weekly_report,
            trigger=CronTrigger(
                day_of_week='mon',
                hour=self.weekly_time.hour,
                minute=self.weekly_time.minute
            ),
            id="weeklyreport_generation",
            name="Weekly Report Generation",
            replace_existing=True
        )
        
        # Schedule monthly report (1st of month at 7:20 AM)
        self.scheduler.add_job(
            self._generate_monthly_report,
            trigger=CronTrigger(
                day=1,
                hour=self.monthly_time.hour,
                minute=self.monthly_time.minute
            ),
            id="monthly_report_generation",
            name="Monthly Report Generation",
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        
        logger.info(
            f"Report scheduler started - Daily: {self.daily_time}, "
            f"Weekly: Mondays {self.weekly_time}, Monthly: 1st {self.monthly_time}"
        )
    
    def stop(self):
        """Stop the scheduler."""
        if not self.is_running:
            logger.warning("Report scheduler is not running")
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("Report scheduler stopped")
    
    async def _generate_daily_report(self):
        """Generate daily report."""
        stats = ReportGenerationStats(report_type="daily")
        
        try:
            logger.info("📊 Starting daily report generation...")
            
            # Get yesterday's date
            target_date = (datetime.utcnow() - timedelta(days=1)).date()
            stats.report_date = target_date
            
            async with get_db() as db:
                generator = ReportGenerator(db)
                
                try:
                    report = await generator.generate_daily_report(target_date)
                    
                    # Save to markdown file
                    filename = f"Daily_Briefing_{target_date.strftime('%Y%m%d')}.md"
                    file_path = os.path.join(self.docs_dir, filename)
                    
                    # Create markdown content
                    markdown = self._convert_daily_report_to_markdown(report)
                    
                    # Save file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(markdown)
                    
                    stats.success = True
                    stats.file_path = file_path
                    stats.end_time = datetime.utcnow()
                    
                    logger.info(
                        f"✅ Daily report generated successfully: {file_path} "
                        f"({stats.duration_seconds:.2f}s)"
                    )
                    
                except ValueError as e:
                    # No analytics data available
                    stats.error_message = str(e)
                    stats.end_time = datetime.utcnow()
                    logger.warning(f"⚠️ Daily report skipped: {e}")
                
        except Exception as e:
            stats.success = False
            stats.error_message = str(e)
            stats.end_time = datetime.utcnow()
            logger.error(f"❌ Daily report generation failed: {e}", exc_info=True)
        
        finally:
            self.last_daily_stats = stats
    
    async def _generate_weekly_report(self):
        """Generate weekly report."""
        stats = ReportGenerationStats(report_type="weekly")
        
        try:
            logger.info("📊 Starting weekly report generation...")
            
            # Get last week's year and week number
            today = datetime.utcnow().date()
            last_week = today - timedelta(days=7)
            year = last_week.isocalendar()[0]
            week_number = last_week.isocalendar()[1]
            stats.report_date = last_week
            
            async with get_db() as db:
                generator = ReportGenerator(db)
                
                try:
                    report = await generator.generate_weekly_report(year, week_number)
                    
                    # Save to markdown file
                    filename = f"Weekly_Report_{last_week.strftime('%Y%m%d')}.md"
                    file_path = os.path.join(self.docs_dir, filename)
                    
                    # Create markdown content
                    markdown = self._convert_weekly_report_to_markdown(report)
                    
                    # Save file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(markdown)
                    
                    stats.success = True
                    stats.file_path = file_path
                    stats.end_time = datetime.utcnow()
                    
                    logger.info(
                        f"✅ Weekly report generated successfully: {file_path} "
                        f"({stats.duration_seconds:.2f}s)"
                    )
                    
                except ValueError as e:
                    stats.error_message = str(e)
                    stats.end_time = datetime.utcnow()
                    logger.warning(f"⚠️ Weekly report skipped: {e}")
                
        except Exception as e:
            stats.success = False
            stats.error_message = str(e)
            stats.end_time = datetime.utcnow()
            logger.error(f"❌ Weekly report generation failed: {e}", exc_info=True)
        
        finally:
            self.last_weekly_stats = stats
    
    async def _generate_monthly_report(self):
        """Generate monthly report."""
        stats = ReportGenerationStats(report_type="monthly")
        
        try:
            logger.info("📊 Starting monthly report generation...")
            
            # Get last month's year and month
            today = datetime.utcnow().date()
            last_month_end = today.replace(day=1) - timedelta(days=1)
            year = last_month_end.year
            month = last_month_end.month
            stats.report_date = last_month_end
            
            async with get_db() as db:
                generator = ReportGenerator(db)
                
                try:
                    report = await generator.generate_monthly_report(year, month)
                    
                    # Save to markdown file
                    filename = f"Monthly_Report_{year}_{month:02d}.md"
                    file_path = os.path.join(self.docs_dir, filename)
                    
                    # Create markdown content
                    markdown = self._convert_monthly_report_to_markdown(report)
                    
                    # Save file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(markdown)
                    
                    stats.success = True
                    stats.file_path = file_path
                    stats.end_time = datetime.utcnow()
                    
                    logger.info(
                        f"✅ Monthly report generated successfully: {file_path} "
                        f"({stats.duration_seconds:.2f}s)"
                    )
                    
                except ValueError as e:
                    stats.error_message = str(e)
                    stats.end_time = datetime.utcnow()
                    logger.warning(f"⚠️ Monthly report skipped: {e}")
                
        except Exception as e:
            stats.success = False
            stats.error_message = str(e)
            stats.end_time = datetime.utcnow()
            logger.error(f"❌ Monthly report generation failed: {e}", exc_info=True)
        
        finally:
            self.last_monthly_stats = stats
    
    def _convert_daily_report_to_markdown(self, report) -> str:
        """Convert DailyReport to markdown."""
        lines = [
            f"# Daily Briefing - {report.report_date.strftime('%Y-%m-%d')}",
            f"",
            f"*Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}*",
            f"",
            f"## Executive Summary",
            f"",
            f"- **Portfolio Value**: ${report.executive_summary.portfolio_value:,.2f}",
            f"- **Daily P&L**: ${report.executive_summary.daily_pnl:,.2f} ({report.executive_summary.daily_return_pct:.2f}%)",
            f"- **Total Return**: {report.executive_summary.total_return_pct:.2f}%",
            f"- **Win Rate**: {report.executive_summary.win_rate * 100:.1f}%",
            f"- **Sharpe Ratio**: {report.executive_summary.sharpe_ratio:.2f}",
            f"- **Positions**: {report.executive_summary.positions_count}",
            f"- **Trades**: {report.executive_summary.trades_count}",
            f"",
        ]
        
        if report.executive_summary.highlights:
            lines.append("### Highlights")
            lines.append("")
            for highlight in report.executive_summary.highlights:
                lines.append(f"- {highlight}")
            lines.append("")
        
        if report.executive_summary.risk_alerts:
            lines.append("### Risk Alerts")
            lines.append("")
            for alert in report.executive_summary.risk_alerts:
                lines.append(f"- {alert}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _convert_weekly_report_to_markdown(self, report) -> str:
        """Convert WeeklyReport to markdown."""
        lines = [
            f"# Weekly Report - {report.year} Week {report.week_number}",
            f"",
            f"*Period: {report.week_start_date} to {report.week_end_date}*",
            f"*Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}*",
            f"",
            f"## Performance Summary",
            f"",
            f"- **Starting Value**: ${report.portfolio_value_start:,.2f}",
            f"- **Ending Value**: ${report.portfolio_value_end:,.2f}",
            f"- **Weekly P&L**: ${report.weekly_pnl:,.2f} ({report.weekly_return_pct:.2f}%)",
            f"- **Total Trades**: {report.total_trades}",
            f"- **Win Rate**: {report.win_rate * 100:.1f}%",
            f"",
            f"## Best & Worst Days",
            f"",
            f"- **Best Day**: {report.best_day_date} (+{report.best_day_return_pct:.2f}%)",
            f"- **Worst Day**: {report.worst_day_date} ({report.worst_day_return_pct:.2f}%)",
            f"",
        ]
        
        return "\n".join(lines)
    
    def _convert_monthly_report_to_markdown(self, report) -> str:
        """Convert MonthlyReport to markdown."""
        lines = [
            f"# Monthly Report - {report.year}-{report.month:02d}",
            f"",
            f"*Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}*",
            f"",
            f"## Performance Summary",
            f"",
            f"- **Starting Value**: ${report.portfolio_value_start:,.2f}",
            f"- **Ending Value**: ${report.portfolio_value_end:,.2f}",
            f"- **Monthly P&L**: ${report.monthly_pnl:,.2f} ({report.monthly_return_pct:.2f}%)",
            f"- **Total Trades**: {report.total_trades}",
            f"- **Trading Days**: {report.trading_days}",
            f"- **Win Rate**: {report.win_rate * 100:.1f}%",
            f"- **Sharpe Ratio**: {report.sharpe_ratio:.2f}",
            f"",
            f"## AI Cost Analysis",
            f"",
            f"- **Total AI Cost**: ${report.total_ai_cost_usd:,.2f}",
            f"- **Total Tokens Used**: {report.total_tokens_used:,}",
            f"",
        ]
        
        return "\n".join(lines)
    
    async def run_manual_daily_report(self) -> ReportGenerationStats:
        """Run manual daily report generation (for testing)."""
        logger.info("Running manual daily report generation")
        await self._generate_daily_report()
        return self.last_daily_stats
    
    def get_last_stats(self) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get last generation statistics for all report types."""
        return {
            "daily": self.last_daily_stats.to_dict() if self.last_daily_stats else None,
            "weekly": self.last_weekly_stats.to_dict() if self.last_weekly_stats else None,
            "monthly": self.last_monthly_stats.to_dict() if self.last_monthly_stats else None,
        }


# Global scheduler instance
_scheduler: Optional[DailyReportScheduler] = None


def get_daily_report_scheduler() -> DailyReportScheduler:
    """
    Get or create daily report scheduler singleton.
    
    Returns:
        DailyReportScheduler instance
    """
    global _scheduler
    
    if _scheduler is None:
        _scheduler = DailyReportScheduler()
    
    return _scheduler


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def demo():
        scheduler = DailyReportScheduler(
            daily_time=time(hour=7, minute=10)
        )
        
        # Run manual daily report for testing
        stats = await scheduler.run_manual_daily_report()
        
        if stats:
            print("\n=== Report Generation Statistics ===")
            print(f"Type: {stats.report_type}")
            print(f"Date: {stats.report_date}")
            print(f"Success: {stats.success}")
            print(f"Duration: {stats.duration_seconds:.2f}s")
            print(f"File: {stats.file_path}")
            if stats.error_message:
                print(f"Error: {stats.error_message}")
        
        # Start scheduler (would run daily at 7:10 AM)
        # scheduler.start()
        # Keep running...
        # await asyncio.sleep(3600)  # Run for 1 hour
        # scheduler.stop()
    
    logging.basicConfig(level=logging.INFO)
    asyncio.run(demo())
