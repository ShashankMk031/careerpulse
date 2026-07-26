from backend.app.repositories.companies import CompaniesRepository
from backend.app.exceptions import NotFoundException, ValidationException
from backend.app.models.entities import CompanyAnalytics

class CompaniesService:
    @staticmethod
    def get_companies(
        conn, page: int, page_size: int, sort_by: str, sort_order: str,
        search: str | None, min_jobs: int | None
    ) -> tuple[list[CompanyAnalytics], int]:
        """
        Orchestrates retrieving paginated company records.
        Validates paging bounds and sort orders.
        """
        if page < 1:
            raise ValidationException("Page number must be greater than or equal to 1.")
        if page_size < 1 or page_size > 100:
            raise ValidationException("Page size must be between 1 and 100.")
        if min_jobs is not None and min_jobs < 0:
            raise ValidationException("Minimum jobs filter cannot be negative.")
            
        offset = (page - 1) * page_size
        return CompaniesRepository.get_companies(
            conn, limit=page_size, offset=offset, sort_by=sort_by,
            sort_order=sort_order, search=search, min_jobs=min_jobs
        )

    @staticmethod
    def get_company_by_name(conn, company: str) -> CompanyAnalytics:
        """
        Retrieves detail lookup for a single company name.
        """
        if not company or not company.strip():
            raise ValidationException("Company name lookup string cannot be blank.")
            
        record = CompaniesRepository.get_company_by_name(conn, company.strip())
        if not record:
            raise NotFoundException(f"Company resource '{company}' not found.")
        return record
