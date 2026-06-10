"""
Log Analyzer Skill - Analyzes audit logs to generate insights and metrics.

Parses structured audit logs and generates metrics including:
- Success rates by component and operation
- Average execution times
- Error frequency and patterns
- Anomaly detection
- System health indicators
"""

from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Any, List
import json
import logging

from skills.base_skill import BaseSkill, SkillInput, SkillOutput

logger = logging.getLogger(__name__)


class LogAnalyzer(BaseSkill):
    """
    Analyzes audit logs to generate insights and metrics.

    Input:
        days (int): Number of days to analyze (default: 7)
        include_anomalies (bool): Include anomaly detection (default: True)

    Output:
        metrics (dict): Comprehensive metrics including:
            - total_events: Total events logged
            - success_rate: Overall success rate
            - avg_duration_ms: Average operation duration
            - error_count: Total errors
            - top_errors: Most common errors
            - component_metrics: Metrics by component
            - hourly_distribution: Events by hour
            - anomalies: Detected anomalies (if enabled)
    """

    SKILL_NAME = "log_analyzer"
    REQUIRES_LLM = False
    DESCRIPTION = "Analyzes audit logs and generates system metrics"

    def execute(self, input_data: SkillInput) -> SkillOutput:
        """Execute log analysis"""
        try:
            # Get parameters
            days = input_data.data.get('days', 7)
            include_anomalies = input_data.data.get('include_anomalies', True)

            logger.info(f"Analyzing audit logs for last {days} days")

            # Load audit logs
            events = self._load_audit_logs(days)

            if not events:
                return SkillOutput(
                    result={'error': 'No audit logs found'},
                    success=False,
                    error_message="No audit logs available for analysis"
                )

            # Generate metrics
            metrics = {
                'period_days': days,
                'analyzed_at': datetime.now().isoformat(),
                'total_events': len(events),
                **self._calculate_overall_metrics(events),
                'component_metrics': self._calculate_component_metrics(events),
                'event_type_distribution': self._calculate_event_distribution(events),
                'hourly_distribution': self._calculate_hourly_distribution(events),
                'error_analysis': self._analyze_errors(events),
                'performance_metrics': self._calculate_performance_metrics(events),
            }

            if include_anomalies:
                metrics['anomalies'] = self._detect_anomalies(events, metrics)

            logger.info(f"Log analysis complete: {metrics['total_events']} events analyzed")

            return SkillOutput(
                result=metrics,
                success=True,
                metadata={'events_analyzed': len(events)}
            )

        except Exception as e:
            logger.error(f"Log analysis failed: {e}", exc_info=True)
            return SkillOutput(
                result=None,
                success=False,
                error_message=str(e)
            )

    def _load_audit_logs(self, days: int) -> List[Dict[str, Any]]:
        """Load audit logs from last N days"""
        audit_dir = Path(self.vault_path) / 'Logs' / 'audit'

        if not audit_dir.exists():
            logger.warning(f"Audit directory not found: {audit_dir}")
            return []

        cutoff_date = datetime.now() - timedelta(days=days)
        events = []

        for log_file in sorted(audit_dir.glob("audit_*.jsonl")):
            try:
                # Extract date from filename
                date_str = log_file.stem.replace('audit_', '')
                file_date = datetime.strptime(date_str, '%Y-%m-%d')

                if file_date < cutoff_date:
                    continue

                # Read events
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            event = json.loads(line.strip())
                            events.append(event)
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                logger.error(f"Failed to read log file {log_file}: {e}")

        return events

    def _calculate_overall_metrics(self, events: List[Dict]) -> Dict[str, Any]:
        """Calculate overall system metrics"""
        total = len(events)
        successful = sum(1 for e in events if e.get('success', True))
        failed = total - successful

        # Calculate average duration
        durations = [e['duration_ms'] for e in events if 'duration_ms' in e]
        avg_duration = sum(durations) / len(durations) if durations else 0

        return {
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'total_successful': successful,
            'total_failed': failed,
            'avg_duration_ms': round(avg_duration, 2),
            'min_duration_ms': min(durations) if durations else 0,
            'max_duration_ms': max(durations) if durations else 0,
        }

    def _calculate_component_metrics(self, events: List[Dict]) -> Dict[str, Dict]:
        """Calculate metrics by component"""
        component_stats = defaultdict(lambda: {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'durations': []
        })

        for event in events:
            component = event.get('component', 'unknown')
            stats = component_stats[component]
            stats['total'] += 1

            if event.get('success', True):
                stats['successful'] += 1
            else:
                stats['failed'] += 1

            if 'duration_ms' in event:
                stats['durations'].append(event['duration_ms'])

        # Calculate averages
        result = {}
        for component, stats in component_stats.items():
            avg_duration = (
                sum(stats['durations']) / len(stats['durations'])
                if stats['durations'] else 0
            )

            result[component] = {
                'total_events': stats['total'],
                'success_rate': (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0,
                'failed_count': stats['failed'],
                'avg_duration_ms': round(avg_duration, 2)
            }

        return result

    def _calculate_event_distribution(self, events: List[Dict]) -> Dict[str, int]:
        """Calculate distribution by event type"""
        distribution = defaultdict(int)
        for event in events:
            event_type = event.get('event_type', 'unknown')
            distribution[event_type] += 1
        return dict(distribution)

    def _calculate_hourly_distribution(self, events: List[Dict]) -> Dict[int, int]:
        """Calculate events by hour of day"""
        hourly = defaultdict(int)

        for event in events:
            try:
                timestamp = datetime.fromisoformat(event['timestamp'])
                hour = timestamp.hour
                hourly[hour] += 1
            except:
                continue

        return dict(sorted(hourly.items()))

    def _analyze_errors(self, events: List[Dict]) -> Dict[str, Any]:
        """Analyze error patterns"""
        error_events = [e for e in events if not e.get('success', True)]

        if not error_events:
            return {
                'total_errors': 0,
                'error_rate': 0,
                'top_errors': [],
                'errors_by_component': {}
            }

        # Count error types
        error_messages = defaultdict(int)
        errors_by_component = defaultdict(int)

        for event in error_events:
            # Get error message
            error_msg = event.get('message', 'Unknown error')
            error_messages[error_msg] += 1

            # Count by component
            component = event.get('component', 'unknown')
            errors_by_component[component] += 1

        # Top 10 errors
        top_errors = sorted(
            [{'message': msg, 'count': count} for msg, count in error_messages.items()],
            key=lambda x: x['count'],
            reverse=True
        )[:10]

        return {
            'total_errors': len(error_events),
            'error_rate': (len(error_events) / len(events) * 100) if events else 0,
            'top_errors': top_errors,
            'errors_by_component': dict(errors_by_component)
        }

    def _calculate_performance_metrics(self, events: List[Dict]) -> Dict[str, Any]:
        """Calculate performance metrics"""
        # Group by operation type
        operation_durations = defaultdict(list)

        for event in events:
            if 'duration_ms' not in event:
                continue

            event_type = event.get('event_type', 'unknown')
            duration = event['duration_ms']
            operation_durations[event_type].append(duration)

        # Calculate percentiles for each operation
        result = {}
        for op_type, durations in operation_durations.items():
            if not durations:
                continue

            sorted_durations = sorted(durations)
            count = len(sorted_durations)

            result[op_type] = {
                'count': count,
                'avg_ms': round(sum(durations) / count, 2),
                'min_ms': round(min(durations), 2),
                'max_ms': round(max(durations), 2),
                'p50_ms': round(sorted_durations[count // 2], 2),
                'p95_ms': round(sorted_durations[int(count * 0.95)], 2) if count > 20 else round(max(durations), 2),
                'p99_ms': round(sorted_durations[int(count * 0.99)], 2) if count > 100 else round(max(durations), 2),
            }

        return result

    def _detect_anomalies(self, events: List[Dict], metrics: Dict) -> List[Dict[str, Any]]:
        """Detect anomalies in system behavior"""
        anomalies = []

        # Anomaly 1: High error rate
        error_rate = metrics.get('error_rate', 0)
        if error_rate > 10:  # More than 10% errors
            anomalies.append({
                'type': 'high_error_rate',
                'severity': 'critical' if error_rate > 20 else 'warning',
                'message': f"Error rate is {error_rate:.1f}% (expected < 10%)",
                'value': error_rate
            })

        # Anomaly 2: Component with very low success rate
        for component, stats in metrics.get('component_metrics', {}).items():
            success_rate = stats['success_rate']
            if success_rate < 80 and stats['total_events'] > 5:
                anomalies.append({
                    'type': 'component_low_success',
                    'severity': 'warning',
                    'message': f"Component '{component}' has {success_rate:.1f}% success rate",
                    'component': component,
                    'value': success_rate
                })

        # Anomaly 3: Unusually slow operations
        for op_type, perf in metrics.get('performance_metrics', {}).items():
            if perf['p95_ms'] > 10000:  # P95 over 10 seconds
                anomalies.append({
                    'type': 'slow_operation',
                    'severity': 'warning',
                    'message': f"Operation '{op_type}' P95 is {perf['p95_ms']:.0f}ms (over 10s threshold)",
                    'operation': op_type,
                    'value': perf['p95_ms']
                })

        # Anomaly 4: No recent events (possible system down)
        recent_events = [e for e in events if self._is_recent(e, hours=1)]
        if len(recent_events) < 5 and len(events) > 100:
            anomalies.append({
                'type': 'low_activity',
                'severity': 'warning',
                'message': f"Only {len(recent_events)} events in last hour (system may be down)",
                'value': len(recent_events)
            })

        return anomalies

    def _is_recent(self, event: Dict, hours: int = 1) -> bool:
        """Check if event is within last N hours"""
        try:
            event_time = datetime.fromisoformat(event['timestamp'])
            cutoff = datetime.now() - timedelta(hours=hours)
            return event_time >= cutoff
        except:
            return False
