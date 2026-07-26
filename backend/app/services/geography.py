from backend.app.repositories.geography import GeographyRepository
from backend.app.models.entities import GeographyAnalytics

class GeographyService:
    @staticmethod
    def get_geography_stats(
        conn, country: str | None, remote: bool | None, sort_by: str, sort_order: str
    ) -> list[GeographyAnalytics]:
        """
        Orchestrates retrieving geographical job market concentrations.
        """
        return GeographyRepository.get_geography(
            conn, country=country, remote=remote, sort_by=sort_by, sort_order=sort_order
        )
