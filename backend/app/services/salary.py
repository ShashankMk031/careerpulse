from backend.app.repositories.salary import SalaryRepository
from backend.app.models.entities import SalaryAnalytics

class SalaryService:
    @staticmethod
    def get_salary_tiers(conn) -> list[SalaryAnalytics]:
        """
        Orchestrates retrieving standard salary bracket summaries.
        """
        return SalaryRepository.get_salary_tiers(conn)
