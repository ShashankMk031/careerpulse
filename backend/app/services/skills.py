from backend.app.repositories.skills import SkillsRepository
from backend.app.exceptions import ValidationException
from backend.app.models.entities import SkillAnalytics

class SkillsService:
    @staticmethod
    def get_skills(
        conn, page: int, page_size: int, sort_by: str, sort_order: str,
        search: str | None, min_demand: int | None
    ) -> tuple[list[SkillAnalytics], int]:
        """
        Orchestrates retrieving paginated skill analytics with filters.
        """
        if page < 1:
            raise ValidationException("Page number must be greater than or equal to 1.")
        if page_size < 1 or page_size > 100:
            raise ValidationException("Page size must be between 1 and 100.")
        if min_demand is not None and min_demand < 0:
            raise ValidationException("Minimum demand count filter cannot be negative.")
            
        offset = (page - 1) * page_size
        return SkillsRepository.get_skills(
            conn, limit=page_size, offset=offset, sort_by=sort_by,
            sort_order=sort_order, search=search, min_demand=min_demand
        )
