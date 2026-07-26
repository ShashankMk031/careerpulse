from backend.app.repositories.technology import TechnologyRepository
from backend.app.exceptions import ValidationException
from backend.app.models.entities import TechnologyAnalytics

class TechnologyService:
    @staticmethod
    def get_technology_analytics(
        conn, page: int, page_size: int, sort_by: str, sort_order: str,
        search: str | None
    ) -> tuple[list[TechnologyAnalytics], int]:
        """
        Orchestrates retrieving paginated technology stack demand records.
        """
        if page < 1:
            raise ValidationException("Page number must be greater than or equal to 1.")
        if page_size < 1 or page_size > 100:
            raise ValidationException("Page size must be between 1 and 100.")
            
        offset = (page - 1) * page_size
        return TechnologyRepository.get_technology(
            conn, limit=page_size, offset=offset, sort_by=sort_by,
            sort_order=sort_order, search=search
        )
