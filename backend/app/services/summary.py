from backend.app.repositories.summary import SummaryRepository
from backend.app.exceptions import NotFoundException
from backend.app.models.entities import HiringSummary, DatasetFreshness

class SummaryService:
    @staticmethod
    def get_dashboard_summary(conn) -> HiringSummary:
        """
        Orchestrates retrieving KPIs. Raises NotFoundException if no snapshots exist.
        """
        summary = SummaryRepository.get_kpis(conn)
        if not summary:
            raise NotFoundException("No hiring analytics summary records found.")
        return summary

    @staticmethod
    def get_dataset_freshness(conn) -> list[DatasetFreshness]:
        """
        Orchestrates retrieving current freshness and lag indicators.
        """
        return SummaryRepository.get_freshness_metrics(conn)
